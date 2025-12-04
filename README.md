# Epub-Reader-Server

《为了一碟醋包的一盘饺子》

一个基于 Python 的简易本地 EPUB 电子书阅读服务器。它将 [epubjs-reader](https://github.com/futurepress/epubjs-reader/) 包装为一个服务器,允许通过浏览器阅读 EPUB 电子书,自动在服务端记录并在不同设备之间同步阅读进度。

- 仓库基于 [epubjs-reader](https://github.com/futurepress/epubjs-reader/) 修改

- 仓库的 reader 目录中除了index.html和reader.js,其它与仓库 [epubjs-reader/reader](https://github.com/futurepress/epubjs-reader/tree/master/reader) 相同

- 运行环境:[在path中的python3.6+](https://www.python.org/),[pyinstaller](https://pyinstaller.org/)

## 使用

1. 克隆仓库
```cmd
git clone https://github.com/heipa24/Epub-Reader-Server.git
cd Epub-Reader-Server
```
2. 将自己的epub重命名`book.epub`然后替换`reader\epub\book.epub`文件
```cmd
copy /y "你自己的epub路径" "%cd%\reader\epub\book.epub"
```
3. 运行*打包为exe.bat*后获得*epub服务器.exe*
```cmd
call "%cd%\打包为exe.bat"
```
4. 运行*epub服务器.exe*,根据提示输入ip和端口号(默认localhost:10086)
```cmd
"%cd%\epub服务器.exe"
```
5. 打开浏览器访问`http://{输入的ip}:{输入的端口号}/`开始阅读自己的epub电子书
```cmd
start "" "http://{输入的ip}:{输入的端口号}/"
```

## 注意

- *epub服务器.exe*会在所在文件夹生成History文件夹,用于记录历史记录,请确保对应一本书的*epub服务器.exe*对应唯一History文件夹
- 每次翻页/打开文章都会在服务端记录,记录只会保存最新的,进度共享:由于历史记录保存在服务端且不区分客户端,**所有连接到此服务器的浏览器在刷新/访问时会跳转到历史记录**。
- **本仓库不适用于多人同时阅读相同的电子书**,否则进度会相互干扰,更适合一个人在不同设备上同步阅读同一本书
