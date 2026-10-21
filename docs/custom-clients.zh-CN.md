# 自定义全平台客户端

默认入口是 **Actions → 自定义全平台客户端 → Run workflow**，每次运行覆盖 Windows、macOS、Linux、Android、iOS，沿用上游支持的架构和打包流程。需要单独构建 Windows x64 时仍可使用原 Windows 入口。

在仓库 **Settings → Secrets and variables → Actions** 配置 Repository variables 或 Repository secrets（同名 Secret 优先）：

| 名称 | 必填 | 内容 |
| --- | --- | --- |
| `RENDEZVOUS_SERVER` | 是 | ID 服务器域名或 IPv4，可附带端口，不带 URL 协议 |
| `RS_PUB_KEY` | 是 | `id_ed25519.pub` 的 Base64 公钥，不能填私钥 |
| `RELAY_SERVER` | 否 | 独立中继服务器域名或 IPv4，可附带端口 |
| `API_SERVER` | 否 | 完整 HTTP(S) API URL，一般只用于 Pro |

所有原生客户端都由 Rust `option_env!` 在编译时嵌入这些配置。Linux 容器会按环境变量名称接收同一组配置；地址和公钥不会拼入 shell 脚本。运行客户端无需访问 GitHub。配置更新后必须重新构建。内置配置是默认值，用户已有的本地设置和外部自定义配置可能优先。

| 平台 | 默认产物及限制 |
| --- | --- |
| Windows | x64/ARM64 Flutter EXE、MSI 模板及 x86 Sciter EXE；无签名服务时输出未签名产物 |
| macOS | Intel/Apple Silicon DMG；无 Apple 证书时输出未签名 DMG |
| Linux | 上游支持的 DEB/RPM、AppImage、Flatpak 等，架构按现有构建矩阵执行 |
| Android | 按 ABI 和 universal APK；无发布签名密钥时上传开发签名 APK，仅供测试，不保证跨次构建可直接覆盖升级 |
| iOS | ARM64 静态库和未签名 `.xcarchive` 压缩包；不是可直接安装的 IPA，需要在 Xcode 使用自己的 Apple 开发团队签名、导出和分发 |

构建期间可在运行页面的 **Artifacts** 下载产物。整次全平台构建成功后，**发布自定义客户端 Release** 工作流会自动汇总最终安装包，在仓库 Releases 创建 `custom-构建序号-运行编号` 版本，并附带 `SHA256SUMS`。它先创建草稿、上传全部文件，完成后再公开发布；失败的构建不会自动发布。

若发布流程临时失败，可在 **Actions → 发布自定义客户端 Release → Run workflow** 填入成功构建的运行编号补发（例如 Actions URL 末尾的数字）。重复触发已发布的同一构建不会重新发布；未完成的草稿可以重试。已过期的 Actions 产物需要重新构建。

发布仅选择最终安装包，不包含桥接代码、裸动态库、Windows 组件目录或 MSI 模板。iOS 未签名归档、Android 开发签名和桌面端签名限制也会写入 Release 说明。原编译工作流中的分散 Release 步骤仍关闭，由单独的汇总发布工作流统一发布；更新元数据仍不发布。

Android 正式发布签名可选配置以下 Secrets：`ANDROID_SIGNING_KEY`（Base64 keystore）、`ANDROID_ALIAS`、`ANDROID_KEY_STORE_PASSWORD`、`ANDROID_KEY_PASSWORD`。macOS 签名沿用上游的 Apple 证书、签名身份和公证配置。iOS 当前明确输出未签名归档，没有自动签名承诺。

连接配置校验在大型编译依赖下载前执行；缺少必填变量时整个构建提前结束。未设置 `custom-client` 的上游调用者仍使用原配置路径。网页客户端是独立实现，不属于这五个原生平台，本入口不构建网页端。

## 验证范围

本地执行配置校验测试与 actionlint；静态检查覆盖全平台入口、复用工作流和容器变量传递。没有服务器配置及各平台运行环境时，不能确认编译成功、签名有效或实际连接成功。每个平台取得安装包后仍需在干净配置下验证服务器注册、连接、安装和重启后的配置保留。

## 现有代码影响

`src/custom_server.rs` 的内置配置函数和 `src/common.rs` 的调用取消 Windows 条件，使桌面及移动端现有的配置加载入口都能读取内置默认值。`flutter-build.yml` 增加默认关闭的自定义构建模式和默认开启的 Release 开关；自定义模式才校验连接配置并增加未签名/开发签名下载产物。上游 workflow 中阻止全平台启动的 universal APK artifact 名称引用和禁用网页作业的条件语法也一并修正。
