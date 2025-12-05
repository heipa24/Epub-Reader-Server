# Epub-Reader-Server

《为了一碟醋包的一盘饺子》

一个基于 Python 的简易本地 EPUB 电子书阅读服务器。它将 [epubjs-reader](https://github.com/futurepress/epubjs-reader/) 包装为一个服务器,允许通过浏览器阅读 EPUB 电子书,自动在服务端记录并在不同设备之间同步阅读进度。 

- 仓库基于 [epubjs-reader](https://github.com/futurepress/epubjs-reader/) 修改
- 仓库的 reader 目录中除了index.html和reader.js,其它与仓库 [epubjs-reader/reader](https://github.com/futurepress/epubjs-reader/tree/master/reader) 相同
- 运行环境:[Windows7+](https://support.microsoft.com/zh-cn/welcometowindows),[在path中的python3.4+](https://www.python.org/),[pyinstaller(pip install pyinstaller)](https://pyinstaller.org/)

## 使用

### 1.克隆仓库(安装了git的话)
```cmd
git clone https://github.com/heipa24/Epub-Reader-Server.git
cd Epub-Reader-Server
```
没有安装git但系统在Windows8及以上的话
```cmd
powershell -Command "$zip='file.zip'; Invoke-WebRequest -Uri https://github.com/heipa24/Epub-Reader-Server/archive/refs/heads/master.zip -OutFile $zip; Expand-Archive -Path $zip -DestinationPath %cd% -Force; Remove-Item $zip"
cd Epub-Reader-Server-master
```
### 2.将自己的epub重命名`book.epub`然后替换`reader\epub\book.epub`文件
```cmd
copy /y "{epub路径}" "%cd%\reader\epub\book.epub"
```
### 3.运行*打包为exe.bat*根据提示输入书名,ip,端口号,获得*epub服务器.exe*
```cmd
call "%cd%\打包为exe.bat"
``` 
### 4.运行`{书名}.exe`会自动使用在`打包为exe.bat`配置的书名,ip,端口号
```cmd
"%cd%\{输入的书名}.exe"
```
### 5.打开浏览器访问`http://{输入的ip}:{输入的端口号}/`开始阅读自己的epub电子书
```cmd
start "" "http://{输入的ip}:{输入的端口号}/"
```

## 注意

- *epub服务器.exe*会在所在文件夹生成History文件夹用于记录历史记录,在History文件夹下有 {书名}.json 文件记录单本书的阅读记录,书名默认为history
- 书名的作用是在History文件夹下区分不同电子书的历史记录,在生成exe时输入的书名会作为exe的文件名(exe的文件名可以放心改),也因为如此会清理书名中不能作为文件/文件夹名的非法字符和书名两头的.和空格(windows下文件名不允许以.结尾,以.开头文件一般认为是隐藏文件,windows下文件名不允许以空格结尾,开头的空格可能为误输入)
- 每次翻页/打开文章都会在服务端记录,记录只会保存最新的,进度共享:由于历史记录保存在服务端且不区分客户端,**所有连接到此服务器的浏览器在刷新/访问时会跳转到历史记录**。
- **本仓库不适用于多人同时阅读相同的电子书**,否则进度会相互干扰,更适合一个人在不同设备上同步阅读同一本书
