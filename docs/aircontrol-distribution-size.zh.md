# Aircontrol 体积构成

- python 解释器

- python 标准库

  包括 pip, setuptools. 但不包括 tkinter.

- aircontrol 依赖库

- 额外准备的常用库

  例如 hidapi, pyserial 等.

这些依赖会通过树摇技术优化, 并使用 7z 最大压缩. 最终的压缩包体积在 15mb 左右.

未来, 会考虑以下方式来进一步压缩空间:

- 使用 micropython 解释器
- 删除部分标准库
- 提供补丁包给用户
- 尽可能复用客户机上已有的资源, 提供定制的安装包