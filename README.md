# Epub-Reader-Server

## 《为了一碟醋包的一盘饺子》

一个基于Python的简易本地EPUB电子书阅读服务器。它将[epubjs-reader](https://github.com/futurepress/epubjs-reader/)包装为一个服务器,允许通过浏览器阅读 EPUB 电子书,自动在服务端记录并在不同设备之间同步阅读进度。

- 仓库基于 [epubjs-reader](https://github.com/futurepress/epubjs-reader/) 修改
- 仓库的 reader 目录中除了index.html和reader.js,其它与仓库 [epubjs-reader/reader](https://github.com/futurepress/epubjs-reader/tree/master/reader) 相同
- 运行环境:[在path中的python3.6+](https://www.python.org/)

### 使用

#### 第1步:克隆仓库并切换到仓库目录

##### **安装了git**

```cmd
git clone https://github.com/heipa24/Epub-Reader-Server.git
cd Epub-Reader-Server
```

##### **没有安装git但系统在Windows8及以上**

```cmd
powershell -Command "$zip='file.zip'; Invoke-WebRequest -Uri https://github.com/heipa24/Epub-Reader-Server/archive/refs/heads/master.zip -OutFile $zip; Expand-Archive -Path $zip -DestinationPath $PWD -Force; Remove-Item $zip"
cd Epub-Reader-Server-master
```

##### 安装了PowerShell Core(PowerShell6及以上)

```bash
pwsh -Command "$zip='file.zip'; Invoke-WebRequest -Uri https://github.com/heipa24/Epub-Reader-Server/archive/refs/heads/master.zip -OutFile $zip; Expand-Archive -Path $zip -DestinationPath $PWD -Force; Remove-Item $zip"
cd Epub-Reader-Server-master
```

### 在windows使用(生成启动脚本)

#### 2.运行`打包为exe.bat`生成启动脚本（根据提示输入书名,ip,端口号,获得`{书名}.bat`）

```cmd
call "%cd%\打包为bat.bat"
```

#### 3.运行`{书名}.bat`放行windows防火墙,浏览器会自动启动,会使用在`打包为bat.bat`配置的书名,ip,端口号

```cmd
call "%cd%\{书名}.bat"
```

### 在windows使用(打包为exe)

#### 2.运行`打包为exe.bat`根据提示输入书名,ip,端口号,获得`{书名}.exe`

```cmd
call "%cd%\打包为exe.bat"
```

#### 3.运行`{书名}.exe`放行windows防火墙,浏览器会自动启动,会使用在`打包为exe.bat`配置的书名,ip,端口号

```cmd
call "%cd%\{书名}.exe"
```

##

### 在Linux/macOS使用(生成启动脚本)

#### 2.运行 `launcher.py` 生成启动脚本（按提示输入书名、ip、端口，会生成 `{书名}.sh`）

```bash
python3 launcher.py
```

#### 3.运行生成的脚本来启动服务器

```bash
./"{书名}.sh"
```

### 第四步其它设备打开浏览器访问 `http://{输入的ip}:{输入的端口}/`开始阅读自己的epub电子书

### 注意

- 在Linux/macOS使用不一定准确,因为这部分被完全交给GitHub Copilot

- `{书名}.exe`会在所在文件夹生成History文件夹用于记录历史记录,在History文件夹下有`{书名}.json`文件记录单本书的阅读记录,通过json文件名区分不同书,**请确保书名唯一避免不同书进度会相互干扰**

- 每次翻页/页面变化都会在服务端记录,记录只会保存最新的,进度共享:由于历史记录保存在服务端且不区分客户端,**所有连接到此服务器的浏览器在刷新/访问时会跳转到历史记录**。

- **本仓库不适用于多人同时阅读相同的电子书**,否则进度会相互干扰,更适合一个人在不同设备上同步阅读

- **如果要移动仓库目录则检查`\reader\epub\staging\.reparse_point`文件是否存在,如果存在则(2选1)**

1. 先将`.reparse_point`文件删除后删除`\reader\epub\staging\`目录,之后将`\staging\`目录复制到`\reader\epub\staging\`(影响打包)

2. 删除`\reader\epub\staging\`后在`\reader\epub\staging\`创建交接点或符号链接指向`\staging\`

- 这是因为创建启动脚本会检查目录`\reader\epub\staging\`是否存在
- 如果存在则将选择的epub文件复制到`\reader\epub\staging\`目录下
- 不存在则创建交接点或符号链接`\reader\epub\staging\`指向`\staging\`目录,并创建`\staging\.reparse_point`,后检查`\reader\epub\staging\.reparse_point`是否存在
- 在打包为exe前会检查`\reader\epub\staging\.reparse_point`是否存在,存在则删除`\reader\epub\staging\`,在打包完成后恢复交接点或符号链接
