"""从已成功的自定义构建汇总安装包，草稿上传完成后再发布。"""

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess


def gh(*args, check=True):
    return subprocess.run(["gh", *args], check=check, capture_output=True, text=True)


def release_artifact(name):
    return name.startswith("custom-") or name.startswith("rustdesk-unsigned-macos-") or (
        name.startswith("rustdesk-") and name.endswith((".deb", ".apk", ".dmg"))
    ) or (name.startswith("windows-") and name.endswith(("-exe", "-msi")))


def collect_assets(downloads, output):
    output.mkdir(parents=True, exist_ok=True)
    hashes = {}
    for source in sorted(downloads.rglob("*")):
        if not source.is_file() or source.is_symlink():
            continue
        if not source.name.endswith((".exe", ".msi", ".dmg", ".deb", ".rpm", ".AppImage", ".flatpak", ".apk", ".pkg.tar.zst", ".xcarchive.tar.gz")):
            continue
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        if source.name in hashes:
            if hashes[source.name] != digest:
                raise ValueError(f"产物文件名冲突：{source.name}")
            continue
        shutil.copyfile(source, output / source.name)
        hashes[source.name] = digest
    if not hashes:
        raise ValueError("未找到可发布的安装包")
    (output / "SHA256SUMS").write_text(
        "".join(f"{hashes[name]}  {name}\n" for name in sorted(hashes)), encoding="utf-8"
    )


def main():
    repo = os.environ["GH_REPO"]
    run_id = os.environ["BUILD_RUN_ID"]
    if not run_id.isdecimal():
        raise ValueError("构建编号必须是数字")
    run = json.loads(gh("api", f"repos/{repo}/actions/runs/{run_id}").stdout)
    if not (
        run["conclusion"] == "success"
        and run["event"] == "workflow_dispatch"
        and run["path"] == ".github/workflows/custom-clients.yml"
        and run["head_branch"] == "master"
        and run["head_repository"]["full_name"] == repo
    ):
        raise ValueError("仅发布本仓库 master 分支已成功完成的全平台自定义构建")
    pages = json.loads(gh("api", "--paginate", "--slurp", f"repos/{repo}/actions/runs/{run_id}/artifacts?per_page=100").stdout)
    artifacts = [a for page in pages for a in page["artifacts"] if release_artifact(a["name"])]
    if not artifacts or any(a["expired"] for a in artifacts):
        raise ValueError("构建产物不存在或已过期")
    workspace = Path("work/custom-release") / run_id
    for artifact in artifacts:
        destination = workspace / "downloads" / str(artifact["id"])
        gh("run", "download", run_id, "--repo", repo, "--name", artifact["name"], "--dir", str(destination))
    output = workspace / "assets"
    collect_assets(workspace / "downloads", output)
    tag = f"custom-{run['run_number']}-{run_id}"
    notes = workspace / "notes.md"
    notes.write_text(
        f"由[全平台构建 #{run['run_number']}]({run['html_url']})生成。\n\n"
        f"源码提交：`{run['head_sha']}`。连接配置在编译时注入。\n\n"
        "Windows/macOS 无发布证书时为未签名版本；Android development APK 使用开发签名；"
        "iOS xcarchive 需要自行使用 Apple 开发者证书签名后导出安装包。\n\n"
        "下载后可使用 SHA256SUMS 校验文件。\n", encoding="utf-8"
    )
    existing = gh("release", "view", tag, "--repo", repo, "--json", "isDraft", check=False)
    if existing.returncode == 0:
        if not json.loads(existing.stdout)["isDraft"]:
            print(f"Release 已发布：{tag}")
            return
    else:
        gh("release", "create", tag, "--repo", repo, "--target", run["head_sha"],
           "--draft", "--title", f"RustDesk 自定义客户端 #{run['run_number']}", "--notes-file", str(notes))
    gh("release", "upload", tag, "--repo", repo, "--clobber", *[str(p) for p in sorted(output.iterdir())])
    gh("release", "edit", tag, "--repo", repo, "--draft=false", "--notes-file", str(notes))
    print(f"Release 已发布：{tag}")


if __name__ == "__main__":
    main()
