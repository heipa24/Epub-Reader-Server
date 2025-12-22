# Epub-Reader-Server

## 《为了一碟醋包的一盘饺子》

一个使用Python编写的简易本地EPUB电子书阅读服务器。它将[epubjs-reader](https://github.com/futurepress/epubjs-reader/)包装为一个服务器,允许通过浏览器阅读 EPUB 电子书,自动在服务端记录并在不同设备之间同步阅读进度。

- 仓库基于 [epubjs-reader](https://github.com/futurepress/epubjs-reader/) 修改
- 仓库的 reader 目录中除了index.html和reader.js,其它与仓库 [epubjs-reader/reader](https://github.com/futurepress/epubjs-reader/tree/master/reader) 相同
- 运行环境:[python3.6+](https://www.python.org/)

### 使用

#### 第1步:克隆仓库并切换到仓库目录

##### **安装了git**

```cmd
git clone https://github.com/heipa24/Epub-Reader-Server.git
cd Epub-Reader-Server
```

##### **系统在Windows8及以上(PowerShell 5.1)**

```cmd
powershell -Command "$zip='file.zip'; iwr -Uri https://github.com/heipa24/Epub-Reader-Server/archive/refs/heads/master.zip -OutFile $zip; Expand-Archive -Path $zip -DestinationPath $PWD -Force; Remove-Item $zip"
cd Epub-Reader-Server-master
```

##### 安装了PowerShell Core(PowerShell 6及以上)

```bash
pwsh -Command "$zip='file.zip'; iwr -Uri https://github.com/heipa24/Epub-Reader-Server/archive/refs/heads/master.zip -OutFile $zip; Expand-Archive -Path $zip -DestinationPath $PWD -Force; del $zip"
cd Epub-Reader-Server-master
```

#### 第2步:生成 /在windows生成可执行文件/在Linux,macOS生成启动脚本

##### 在windows生成启动脚本:运行`打包为bat.bat`根据提示输入书名,ip,端口号,获得`{书名}.bat`

```cmd
call "%cd%\打包为bat.bat"
```

##### 在windows生成应用程序:运行`打包为exe.bat`根据提示输入书名,ip,端口号,获得`{书名}.exe`

```cmd
call "%cd%\打包为exe.bat"
```

##### 在在Linux/macOS生成启动脚本:运行`打包为exe.bat`根据提示输入书名,ip,端口号,获得`{书名}.sh`

```bash
python3 launcher.py
```

#### 第3步:运行`{书名}.bat`/`{书名}.exe`/`{书名}.sh`浏览器会自动启动,会使用在`第2步`配置的书名,ip,端口号

```cmd
call "%cd%\{书名}.bat"
```

```cmd
call "%cd%\{书名}.exe"
```

```bash
./"{书名}.sh"
```

#### 第4步:其它设备打开浏览器访问 `http://{输入的ip}:{输入的端口}/`开始阅读自己的epub电子书

### 注意

- 在Linux/macOS使用不一定准确,因为这部分被完全交给GitHub Copilot

- `{书名}.exe`会在所在文件夹生成History文件夹用于记录历史记录,在History文件夹下有`{书名}.json`文件记录单本书的阅读记录,通过json文件名区分不同书,**请确保书名唯一避免不同书进度会相互干扰,移动exe/bat/sh/py时请将History文件夹一起移动**

- 每次翻页/页面变化都会在服务端记录,记录只会保存最新的,进度共享:由于历史记录保存在服务端且不区分客户端,**所有连接到此服务器的浏览器在刷新/访问时会跳转到历史记录**。

- **本仓库不适用于多人同时阅读相同的电子书**,否则进度会相互干扰,更适合一个人在不同设备上同步阅读

- **如果要移动了仓库则需执行`修复.bat`或`修复.sh`恢复交接点/符号链接**因为生成启动脚本时将选择的epub复制到`\staging\`目录,后使用交接点/符号链接`\reader\epub\staging\`指向`\staging\`
