PowerRename OCR Engine

此目录用于存放内置OCR组件。

目录结构：

engine/
 |
 |-- tesseract.exe
 |
 |-- tessdata/
      |
      |-- chi_sim.traineddata

说明：
1. tesseract.exe 为OCR识别程序。
2. tessdata用于存放中文识别语言包。
3. 发布绿色版时，此目录必须与PowerRename.exe保持同级。
4. 缺少此目录会导致OCR识别失败。
