# Iruka Remote (远程开发环境)

[![许可证: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

一个基于Web界面的工具，用于在Docker容器中创建和管理隔离的、由AI驱动的开发环境。该工具旨在简化您的AI驱动开发工作流程，让您可以在几秒钟内启动与Git仓库关联的全新、干净的编码环境。

每个环境都预先配置了Git、Node.js和您选择的AI工具（Google Gemini 或 Anthropic Claude），使您只需点击几下，就能从一个Git分支进入一个完全交互式的AI编码会话。

## 核心功能

- **基于项目的管理**：将您的工作组织成项目，每个项目都链接到一个Git仓库。
    - **多AI支持**：在每个环境的基础上选择**Google Gemini**或**Anthropic Claude**，让您能为不同任务选择最合适的工具。
    - **隔离的Docker环境**：在每个项目中创建多个独立的开发环境（Docker容器）。
    - **灵活的分支策略**：
        - 从**现有的远程分支**启动一个环境，以修复错误或协作开发功能。
        - 通过创建**新的本地和远程分支**来启动一个环境，非常适合开始新功能的开发。
    - **自动化环境设置**：每个新环境都会自动：
        1.  克隆项目的Git仓库。
        2.  检出指定的分支或创建一个新分支。
        3.  将新分支推送到远程仓库，以便立即进行协作。
        4.  预装 `git`、`nodejs`、`npm` 和选定的AI CLI工具。
    - **集成式Web终端**：在您的浏览器中提供一个完全交互式的 `xterm.js` 终端，直接连接到环境的shell。
    - **无缝的AI集成**：点击一个正在运行的环境，将直接进入所选AI的交互式CLI，准备进行AI驱动的开发。
    - **集中化配置**：在项目级别安全地管理您的API令牌（Git、Gemini、Anthropic）。
    - **性能与可靠性**：通过缓存远程Git分支来加快环境创建速度，并为网络操作提供强大的超时处理。

## 技术栈

- **前端**：
    - **框架**：React (使用Vite)
    - **UI库**：Material-UI
    - **终端**：Xterm.js
- **后端**：
    - **框架**：Python 3 与 FastAPI
    - **Docker交互**：`docker-py`
    - **实时通信**：WebSockets
    - **WSGI服务器**：Uvicorn
- **核心自动化**：
    - Docker容器化
    - 用于环境配置的Shell脚本

## 快速入门

### 先决条件

- **Docker**：Docker守护进程必须在运行后端的机器上运行。
- **Python**：Python 3.10+ 并安装 `venv`。
- **Node.js**：Node.js 20+ 并安装 `npm`。
- **一个Git仓库**，其中包含一个 `Dockerfile`（一个简单的 `ubuntu:latest` 或 `python:latest` 基础镜像即可）。

### 安装与启动

您将需要两个独立的终端会话来分别运行后端和前端服务器。

**1. 后端服务器：**

```bash
# 导航到后端目录
cd ./backend

# 创建Python虚拟环境
python3 -m venv venv

# 激活虚拟环境
# 在 macOS/Linux 上:
# source venv/bin/activate
# 在 Windows 上:
# venv\\Scripts\\activate

# 安装所需的Python包
pip install -r requirements.txt

# 运行FastAPI服务器
uvicorn app.main:app --reload
```
后端将在 `http://localhost:8000` 上运行。

**2. 前端服务器：**

```bash
# 导航到前端目录
cd ./frontend

# 安装所需的npm包
npm install

# 运行Vite开发服务器
npm run dev
```
前端将可以通过 `http://localhost:5173`（或下一个可用端口）访问。

## 如何使用

1.  **创建项目**：
        - 在浏览器中打开Web UI。
        - 点击“New Project”（新建项目）。
        - 填写项目名称和您的Git仓库的 **HTTPS URL**。
        - （可选）添加您的Git个人访问令牌（私有仓库需要）以及您的Gemini和/或Claude的API密钥。
    2.  **打开项目工作区**：
        - 从顶部标题栏的下拉菜单中选择您新创建的项目。
    3.  **管理设置（可选）**：
        - 在工作区中，您可以展开“Project Settings”（项目设置）区域，随时添加或更新您的Git、Gemini和Anthropic API令牌。
    4.  **创建新环境**：
        - 在左侧边栏中，点击“**+ New**”（新建）按钮。
        - 为您的环境命名（例如，`feature-new-login`）。
        - 选择您的分支策略：
            - **Create new branch**（创建新分支）：将本地创建一个名为 `feature/<您的环境名称>` 的新分支，并将其推送到您的远程仓库。
            - **Use existing branch**（使用现有分支）：从所有可用远程分支的下拉列表中选择一个分支（此列表已缓存以提高性能）。
        - 选择您期望的**AI工具**（Gemini或Claude）。
        - 为环境选择一个基础Docker镜像（例如，`ubuntu:latest`）。
        - 点击“Create”（创建）。
    5.  **连接到AI Shell**：
        - 等待环境状态变为“running”（运行中）。这可能需要几分钟时间来安装依赖项。
        - 在左侧边栏中点击正在运行的环境。
        - 右侧的终端将连接并将您直接带入所选AI的交互式shell，准备开始编码。

## 许可证

本项目根据 **GNU通用公共许可证v3.0** 进行许可。

该强力copyleft许可证的权限取决于在相同许可证下提供许可作品和修改（包括使用许可作品的更大型作品）的完整源代码。版权和许可证声明必须保留。贡献者提供明确的专利权授予。有关完整详情，请参阅[LICENSE](LICENSE)文件。
