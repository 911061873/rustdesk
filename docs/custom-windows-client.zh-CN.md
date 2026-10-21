# 编译内置服务器配置的 Windows 客户端

默认构建全部平台请参阅 [全平台编译说明](custom-clients.zh-CN.md)。本入口仅用于单独构建 Windows x64。

在 fork 仓库的 **Settings → Secrets and variables → Actions** 中添加以下 Repository secrets 或 Repository variables。同名 Secret 优先。

| 名称 | 必填 | 内容 |
| --- | --- | --- |
| `RENDEZVOUS_SERVER` | 是 | ID 服务器域名或 IPv4 地址，可附带端口，例如 `rd.example.com:21116`，不带 `http://` |
| `RS_PUB_KEY` | 是 | 自建服务器 `id_ed25519.pub` 中的 Base64 公钥，不是私钥 |
| `RELAY_SERVER` | 否 | 独立中继服务器域名或 IPv4 地址，可附带端口；留空使用 ID 服务器返回的中继信息 |
| `API_SERVER` | 否 | 使用 Pro API 时填写完整 HTTP(S) URL；OSS 服务一般留空 |

打开 **Actions → 自定义 Windows 客户端 → Run workflow**，选择包含本改动的分支。首次 fork 时如 Actions 被禁用，先启用仓库工作流。

构建完成后，在本次运行的 Artifacts 下载 **rustdesk-custom-windows-x64-exe**，解压获得单文件 EXE。构建只上传 Actions artifact，不自动发布 Release；保留期为 14 天。客户端未签名。构建复用上游固定版本的 Flutter、Rust、vcpkg 和 Windows 打包流程。

服务器地址和公钥由 Actions 注入编译环境，Rust `option_env!` 在编译时将它们嵌入客户端。改名、移动 EXE 不会丢失内置配置；运行时无需访问 GitHub，也无需随附 `custom.txt`。修改仓库变量后必须重新编译并分发 EXE。

内置值属于默认配置，已有本地网络配置、文件名配置或外部自定义配置可能优先。首次验证应使用干净的 Windows 用户配置；如旧客户端仍使用旧服务器，在网络设置中修改或清除旧配置后再验证。安装、服务、托盘与 GUI 都经过相同的客户端配置加载入口。

缺少地址、公钥或公钥格式无效会在下载大型编译依赖前报错。Secrets 能避免配置直接出现在 workflow 文件中，但地址、公钥最终可从 EXE 提取，不应将私钥、访问令牌或无人值守密码嵌入本构建。

## 验证

本地配置校验测试：`python -m unittest discover -s res -p test_validate_custom_server.py`。Windows 构建工作流在构建后执行与发布特性一致的 Rust 单元测试和 clipboard 包测试，随后生成 EXE。

拿到实际 EXE 后还需在干净 Windows 环境确认网络设置、ID 注册、与另一客户端建立远程连接，以及安装后的服务连接。配置格式校验和 CI 编译成功不能替代真实服务器连通性验证。

## 改动范围

现有代码仅修改 `src/common.rs` 的自定义配置加载入口，增加通用的一行调用，以及 `src/custom_server.rs` 的内置配置加载函数。未设置构建环境变量时直接返回，沿用原流程；共享子模块与上游通用构建流程保持原样；桥接工作流仅将停用的 v3 缓存 action 升级为 v4。
