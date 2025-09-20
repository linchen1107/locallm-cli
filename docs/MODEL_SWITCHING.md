# 模型切換功能指南

LocalLM CLI 提供靈活的模型切換功能，讓您可以在不同的 AI 模型之間輕鬆切換。

## 🔄 基本使用

### 查看當前模型
```bash
/model
```

### 查看所有可用模型
```bash
/models
```

### 切換模型
```bash
# 使用完整模型名稱
/model llama3.2:latest

# 使用簡短別名
/model llama

# 使用數字選擇
/model 5
```

## 🏷️ 支援的別名

為了方便使用，系統支援以下模型別名：

- `llama` → `llama3.2:latest`
- `llama3` → `llama3.2:latest`
- `mistral` → `mistral:7b`
- `codellama` → `codellama:13b`
- `gemma` → `gemma3:12b`
- `phi` → `phi4:14b`
- `qwen` → `qwen3:8b`
- `deepseek` → `deepseek-r1:8b`

## 🎯 使用場景

### 1. 程式開發
```bash
/model codellama    # 切換到程式碼專用模型
```

### 2. 一般對話
```bash
/model llama       # 切換到通用對話模型
```

### 3. 多語言處理
```bash
/model qwen        # 切換到多語言支援模型
```

### 4. 快速選擇
```bash
/models            # 查看編號列表
/model 3           # 選擇第3個模型
```

## 💡 進階功能

### 模糊匹配
如果您輸入的模型名稱不完全匹配，系統會提供建議：

```bash
/model code
# ❌ Model 'code' not found
# 📝 Did you mean:
#    - codellama:13b
```

### 自動清理對話歷史
切換模型時，系統會自動清空對話歷史，確保不同模型之間不會有衝突。

### 當前模型標示
在模型列表中，當前使用的模型會被特別標示：
```
19. mistral:7b (4.1GB) ← current
```

## 🚀 實用技巧

1. **快速切換**: 使用數字選擇是最快的切換方式
2. **別名記憶**: 記住常用的別名，如 `llama`, `mistral`
3. **模型特性**: 不同模型有不同的專長，選擇合適的模型提升效果
4. **資源考量**: 注意模型大小，大模型需要更多記憶體

## ⚙️ 設定建議

根據不同任務選擇合適的模型：

- **文字創作**: `llama3.2:latest`
- **程式碼**: `codellama:13b`  
- **數學推理**: `phi4:14b`
- **多語言**: `qwen3:8b`
- **快速回應**: `mistral:7b`

記住，您可以隨時使用 `/model` 查看當前模型，使用 `/models` 查看所有可用選項！