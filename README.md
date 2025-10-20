# 学习视频分享平台 (Learning Video Platform)

一个基于 React Native + Expo 的跨平台学习视频分享应用，支持视频播放、学习进度跟踪、内容上传和社交互动功能。

## 🚀 项目特性

### 核心功能
- **视频播放与学习**: 支持多种视频格式播放，实时学习进度跟踪
- **内容发现**: 首页 Feed 流，支持按标签、语言筛选搜索
- **内容创作**: 视频上传流程，支持本地文件选择和元数据编辑
- **社交互动**: 评论系统、作者主页、收藏和稍后看功能
- **学习管理**: 个人学习进度、历史记录、收藏管理

### 技术栈
- **框架**: React Native 0.81.4 + Expo ~54.0
- **导航**: React Navigation v7 (Stack + Bottom Tabs)
- **UI 组件**: React Native Paper + Material Icons
- **状态管理**: Redux Toolkit + React Redux
- **视频播放**: Expo AV
- **数据持久化**: AsyncStorage
- **表单处理**: React Hook Form + Zod 验证
- **动画**: React Native Reanimated v4

## 📱 应用结构

### 主要页面
```
├── 首页 (Home Feed)
│   ├── 视频列表展示
│   ├── 视频详情播放页
│   ├── 评论页面
│   └── 作者主页
├── 搜索 (Search)
│   ├── 搜索界面 (标签筛选)
│   └── 搜索结果页
├── 上传 (Upload)
│   ├── 媒体选择页
│   ├── 视频信息编辑
│   └── 发布确认
├── 消息 (Messages)
│   └── 消息列表
└── 我的 (Profile)
    ├── 个人信息
    ├── 学习进度
    └── 收藏管理
```

### 核心组件功能

#### 视频播放器
- 支持 HLS (.m3u8) 和 MP4 格式
- 实时播放进度跟踪和保存
- 播放控制 (播放/暂停/进度条)
- 学习进度可视化展示

#### 搜索与筛选
- 按标签分类筛选 (算法、英语、前端等)
- 按语言筛选 (中文/英文)
- 实时搜索结果展示

#### 上传流程
- 本地文件选择 (支持视频格式)
- 视频信息编辑 (标题、描述、标签)
- 发布前预览确认

## 🛠️ 开发环境设置

### 系统要求
- **Node.js**: >= 18.0.0 (推荐 20.19.4+)
- **npm**: >= 8.0.0
- **Expo CLI**: 最新版本
- **操作系统**: macOS, Windows, Linux

### 安装步骤

1. **克隆项目**
   ```bash
   git clone https://github.com/cherloner/my-project.git
   cd my-project
   ```

2. **安装依赖**
   ```bash
   npm install
   ```

3. **启动开发服务器**
   ```bash
   # 启动 Expo 开发服务器
   npm start
   
   # 或者直接启动特定平台
   npm run android    # Android 模拟器
   npm run ios        # iOS 模拟器  
   npm run web        # Web 浏览器
   ```

4. **在设备上运行**
   - **移动设备**: 下载 Expo Go App，扫描二维码
   - **Web 浏览器**: 访问 http://localhost:8081
   - **模拟器**: 按 `a` (Android) 或 `i` (iOS)

## 📋 可用脚本

```bash
npm start          # 启动 Expo 开发服务器
npm run android    # 在 Android 设备/模拟器运行
npm run ios        # 在 iOS 设备/模拟器运行  
npm run web        # 在 Web 浏览器运行
```

## 🔧 项目配置

### 重要配置文件
- `app.json` - Expo 应用配置
- `babel.config.js` - Babel 编译配置 (包含 Reanimated 插件)
- `tsconfig.json` - TypeScript 配置
- `package.json` - 依赖管理和脚本

### 环境变量
项目当前使用模拟数据，生产环境需要配置：
- API 服务器地址
- 视频存储服务 (如 AWS S3, 阿里云 OSS)
- 用户认证服务

## 🚨 已知问题与解决方案

### Node.js 版本警告
```
npm warn EBADENGINE Unsupported engine
```
**解决方案**: 升级 Node.js 到 20.19.4+ 版本

### react-native-screens 版本不兼容
```
react-native-screens@4.17.1 is not compatible with current Expo version
```
**解决方案**: 
```bash
npm install react-native-screens@~4.16.0
```

### Web 端 Reanimated 插件错误
已在 `babel.config.js` 中配置条件加载，Web 端会跳过 Reanimated 插件。

## 🤝 协同开发指南

### 分支管理
- `main` - 主分支 (受保护，需要 PR)
- `feature/*` - 功能开发分支
- `bugfix/*` - 问题修复分支

### 提交规范
```bash
feat: 新功能
fix: 问题修复  
docs: 文档更新
style: 代码格式调整
refactor: 代码重构
test: 测试相关
chore: 构建/工具链更新
```

### 开发流程
1. 从 `main` 分支创建功能分支
2. 开发完成后提交 Pull Request
3. 代码审查通过后合并到 `main`

### 调试技巧
- 使用 Expo DevTools 进行调试
- React Native Debugger 用于复杂调试
- 控制台日志: `console.log()` 在 Metro 终端显示

## 📚 扩展开发

### 添加新页面
1. 在 `App.tsx` 中创建新的 Screen 组件
2. 添加到对应的 Stack Navigator
3. 更新导航类型定义

### 集成后端 API
1. 替换 `mockVideos` 数据为 API 调用
2. 添加网络请求库 (如 axios)
3. 实现用户认证和状态管理

### 部署发布
```bash
# 构建生产版本
expo build:android
expo build:ios
expo build:web

# 发布到 Expo
expo publish
```

## 📄 许可证

本项目仅用于学习和开发目的。

## 🆘 获取帮助

如遇到问题，请：
1. 查看 [Expo 官方文档](https://docs.expo.dev/)
2. 检查 [React Navigation 文档](https://reactnavigation.org/)
3. 在项目 Issues 中提问
4. 联系项目维护者

---

**快速开始**: `npm install && npm start` 🚀