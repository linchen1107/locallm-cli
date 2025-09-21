"""
數據可視化工具
支援 CSV 和 Excel 文件的圖表生成
"""

import os
import json
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

# 可選依賴檢查
try:
    import pandas as pd
    import matplotlib.pyplot as plt
    import seaborn as sns
    HAS_PANDAS = True
    HAS_MATPLOTLIB = True
    HAS_SEABORN = True
except ImportError:
    HAS_PANDAS = False
    HAS_MATPLOTLIB = False
    HAS_SEABORN = False

try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.offline import plot
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

class DataVisualizer:
    """數據可視化器"""
    
    def __init__(self):
        self.supported_formats = ['.csv', '.xlsx', '.xls']
        self.output_dir = "charts"
        self._ensure_output_dir()
    
    def _ensure_output_dir(self):
        """確保輸出目錄存在"""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
    
    def check_dependencies(self) -> Dict[str, bool]:
        """檢查可視化依賴"""
        return {
            'pandas': HAS_PANDAS,
            'matplotlib': HAS_MATPLOTLIB,
            'seaborn': HAS_SEABORN,
            'plotly': HAS_PLOTLY
        }
    
    def analyze_data_structure(self, file_path: str) -> Dict[str, Any]:
        """分析數據結構"""
        if not HAS_PANDAS:
            return {"error": "pandas 未安裝，無法分析數據結構"}
        
        try:
            # 根據文件擴展名選擇讀取方法
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            elif file_path.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file_path)
            else:
                return {"error": f"不支援的文件格式: {file_path}"}
            
            # 基本統計信息
            analysis = {
                "file_path": file_path,
                "shape": df.shape,
                "columns": df.columns.tolist(),
                "data_types": df.dtypes.to_dict(),
                "missing_values": df.isnull().sum().to_dict(),
                "numeric_columns": df.select_dtypes(include=['number']).columns.tolist(),
                "categorical_columns": df.select_dtypes(include=['object']).columns.tolist(),
                "datetime_columns": df.select_dtypes(include=['datetime']).columns.tolist(),
                "sample_data": df.head(3).to_dict('records')
            }
            
            # 數值列的統計信息
            if analysis["numeric_columns"]:
                analysis["numeric_stats"] = df[analysis["numeric_columns"]].describe().to_dict()
            
            return analysis
            
        except Exception as e:
            return {"error": f"分析數據結構失敗: {str(e)}"}
    
    def suggest_charts(self, analysis: Dict[str, Any]) -> List[Dict[str, str]]:
        """根據數據結構建議圖表類型"""
        suggestions = []
        
        if "error" in analysis:
            return suggestions
        
        numeric_cols = analysis.get("numeric_columns", [])
        categorical_cols = analysis.get("categorical_columns", [])
        datetime_cols = analysis.get("datetime_columns", [])
        
        # 基於數據類型建議圖表
        if len(numeric_cols) >= 1:
            if len(numeric_cols) == 1:
                suggestions.extend([
                    {"type": "histogram", "name": "直方圖", "description": f"顯示 {numeric_cols[0]} 的分布"},
                    {"type": "box", "name": "箱線圖", "description": f"顯示 {numeric_cols[0]} 的統計分布"}
                ])
            elif len(numeric_cols) >= 2:
                suggestions.extend([
                    {"type": "scatter", "name": "散點圖", "description": f"顯示 {numeric_cols[0]} 與 {numeric_cols[1]} 的關係"},
                    {"type": "line", "name": "線圖", "description": f"顯示 {numeric_cols[0]} 與 {numeric_cols[1]} 的趨勢"}
                ])
        
        if len(categorical_cols) >= 1:
            suggestions.extend([
                {"type": "bar", "name": "柱狀圖", "description": f"顯示 {categorical_cols[0]} 的計數"},
                {"type": "pie", "name": "餅圖", "description": f"顯示 {categorical_cols[0]} 的比例"}
            ])
        
        if len(numeric_cols) >= 1 and len(categorical_cols) >= 1:
            suggestions.extend([
                {"type": "box_categorical", "name": "分類箱線圖", "description": f"按 {categorical_cols[0]} 分組顯示 {numeric_cols[0]} 的分布"},
                {"type": "bar_grouped", "name": "分組柱狀圖", "description": f"按 {categorical_cols[0]} 分組顯示數值統計"}
            ])
        
        if len(datetime_cols) >= 1 and len(numeric_cols) >= 1:
            suggestions.extend([
                {"type": "time_series", "name": "時間序列圖", "description": f"顯示 {datetime_cols[0]} 與數值的時間趨勢"}
            ])
        
        return suggestions
    
    def create_chart(self, file_path: str, chart_type: str, 
                    x_column: str = None, y_column: str = None,
                    title: str = None, save_path: str = None) -> Dict[str, Any]:
        """創建圖表"""
        if not HAS_PANDAS or not HAS_MATPLOTLIB:
            return {"error": "缺少必要的依賴: pandas, matplotlib"}
        
        try:
            # 讀取數據
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            elif file_path.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file_path)
            else:
                return {"error": f"不支援的文件格式: {file_path}"}
            
            # 設置圖表樣式
            plt.style.use('seaborn-v0_8' if HAS_SEABORN else 'default')
            plt.figure(figsize=(12, 8))
            
            # 生成圖表
            chart_info = self._generate_chart(df, chart_type, x_column, y_column, title)
            
            # 保存圖表
            if save_path is None:
                save_path = os.path.join(self.output_dir, f"{Path(file_path).stem}_{chart_type}.png")
            
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            return {
                "success": True,
                "chart_type": chart_type,
                "save_path": save_path,
                "info": chart_info
            }
            
        except Exception as e:
            return {"error": f"創建圖表失敗: {str(e)}"}
    
    def _generate_chart(self, df: pd.DataFrame, chart_type: str, 
                        x_column: str = None, y_column: str = None, 
                        title: str = None) -> Dict[str, Any]:
        """生成具體的圖表"""
        info = {"chart_type": chart_type}
        
        if chart_type == "histogram":
            if not x_column:
                x_column = df.select_dtypes(include=['number']).columns[0]
            plt.hist(df[x_column].dropna(), bins=30, alpha=0.7, edgecolor='black')
            plt.xlabel(x_column)
            plt.ylabel('頻率')
            plt.title(title or f'{x_column} 的分布')
            info.update({"x_column": x_column, "bins": 30})
        
        elif chart_type == "scatter":
            numeric_cols = df.select_dtypes(include=['number']).columns
            if not x_column:
                x_column = numeric_cols[0]
            if not y_column:
                y_column = numeric_cols[1] if len(numeric_cols) > 1 else numeric_cols[0]
            plt.scatter(df[x_column], df[y_column], alpha=0.6)
            plt.xlabel(x_column)
            plt.ylabel(y_column)
            plt.title(title or f'{x_column} vs {y_column}')
            info.update({"x_column": x_column, "y_column": y_column})
        
        elif chart_type == "line":
            numeric_cols = df.select_dtypes(include=['number']).columns
            if not x_column:
                x_column = numeric_cols[0]
            if not y_column:
                y_column = numeric_cols[1] if len(numeric_cols) > 1 else numeric_cols[0]
            plt.plot(df[x_column], df[y_column], marker='o')
            plt.xlabel(x_column)
            plt.ylabel(y_column)
            plt.title(title or f'{x_column} vs {y_column}')
            info.update({"x_column": x_column, "y_column": y_column})
        
        elif chart_type == "bar":
            if not x_column:
                x_column = df.select_dtypes(include=['object']).columns[0]
            value_counts = df[x_column].value_counts()
            plt.bar(range(len(value_counts)), value_counts.values)
            plt.xticks(range(len(value_counts)), value_counts.index, rotation=45)
            plt.xlabel(x_column)
            plt.ylabel('計數')
            plt.title(title or f'{x_column} 的計數')
            info.update({"x_column": x_column, "categories": len(value_counts)})
        
        elif chart_type == "pie":
            if not x_column:
                x_column = df.select_dtypes(include=['object']).columns[0]
            value_counts = df[x_column].value_counts()
            plt.pie(value_counts.values, labels=value_counts.index, autopct='%1.1f%%')
            plt.title(title or f'{x_column} 的比例')
            info.update({"x_column": x_column, "categories": len(value_counts)})
        
        elif chart_type == "box":
            if not x_column:
                x_column = df.select_dtypes(include=['number']).columns[0]
            plt.boxplot(df[x_column].dropna())
            plt.ylabel(x_column)
            plt.title(title or f'{x_column} 的箱線圖')
            info.update({"x_column": x_column})
        
        elif chart_type == "box_categorical":
            categorical_cols = df.select_dtypes(include=['object']).columns
            numeric_cols = df.select_dtypes(include=['number']).columns
            if not x_column:
                x_column = categorical_cols[0]
            if not y_column:
                y_column = numeric_cols[0]
            
            # 分組箱線圖
            groups = df.groupby(x_column)[y_column].apply(list)
            plt.boxplot(groups.values, labels=groups.index)
            plt.xlabel(x_column)
            plt.ylabel(y_column)
            plt.title(title or f'按 {x_column} 分組的 {y_column} 分布')
            plt.xticks(rotation=45)
            info.update({"x_column": x_column, "y_column": y_column, "groups": len(groups)})
        
        else:
            raise ValueError(f"不支援的圖表類型: {chart_type}")
        
        return info
    
    def create_interactive_chart(self, file_path: str, chart_type: str,
                               x_column: str = None, y_column: str = None,
                               title: str = None, save_path: str = None) -> Dict[str, Any]:
        """創建互動式圖表（使用 Plotly）"""
        if not HAS_PLOTLY or not HAS_PANDAS:
            return {"error": "缺少必要的依賴: plotly, pandas"}
        
        try:
            # 讀取數據
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            elif file_path.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file_path)
            else:
                return {"error": f"不支援的文件格式: {file_path}"}
            
            # 生成互動式圖表
            fig = self._generate_interactive_chart(df, chart_type, x_column, y_column, title)
            
            # 保存圖表
            if save_path is None:
                save_path = os.path.join(self.output_dir, f"{Path(file_path).stem}_{chart_type}_interactive.html")
            
            fig.write_html(save_path)
            
            return {
                "success": True,
                "chart_type": chart_type,
                "save_path": save_path,
                "interactive": True
            }
            
        except Exception as e:
            return {"error": f"創建互動式圖表失敗: {str(e)}"}
    
    def _generate_interactive_chart(self, df: pd.DataFrame, chart_type: str,
                                   x_column: str = None, y_column: str = None,
                                   title: str = None):
        """生成互動式圖表"""
        if chart_type == "scatter":
            numeric_cols = df.select_dtypes(include=['number']).columns
            if not x_column:
                x_column = numeric_cols[0]
            if not y_column:
                y_column = numeric_cols[1] if len(numeric_cols) > 1 else numeric_cols[0]
            fig = px.scatter(df, x=x_column, y=y_column, title=title or f'{x_column} vs {y_column}')
        
        elif chart_type == "line":
            numeric_cols = df.select_dtypes(include=['number']).columns
            if not x_column:
                x_column = numeric_cols[0]
            if not y_column:
                y_column = numeric_cols[1] if len(numeric_cols) > 1 else numeric_cols[0]
            fig = px.line(df, x=x_column, y=y_column, title=title or f'{x_column} vs {y_column}')
        
        elif chart_type == "bar":
            if not x_column:
                x_column = df.select_dtypes(include=['object']).columns[0]
            value_counts = df[x_column].value_counts()
            fig = px.bar(x=value_counts.index, y=value_counts.values, 
                        title=title or f'{x_column} 的計數')
        
        elif chart_type == "pie":
            if not x_column:
                x_column = df.select_dtypes(include=['object']).columns[0]
            value_counts = df[x_column].value_counts()
            fig = px.pie(values=value_counts.values, names=value_counts.index,
                        title=title or f'{x_column} 的比例')
        
        else:
            # 回退到基本散點圖
            numeric_cols = df.select_dtypes(include=['number']).columns
            if len(numeric_cols) >= 2:
                fig = px.scatter(df, x=numeric_cols[0], y=numeric_cols[1])
            else:
                fig = px.bar(df, title="數據概覽")
        
        return fig
    
    def batch_create_charts(self, file_path: str, chart_types: List[str] = None) -> Dict[str, Any]:
        """批量創建圖表"""
        if not chart_types:
            # 分析數據並建議圖表類型
            analysis = self.analyze_data_structure(file_path)
            if "error" in analysis:
                return analysis
            
            suggestions = self.suggest_charts(analysis)
            chart_types = [s["type"] for s in suggestions[:3]]  # 取前3個建議
        
        results = []
        for chart_type in chart_types:
            result = self.create_chart(file_path, chart_type)
            results.append(result)
        
        return {
            "file_path": file_path,
            "charts_created": len([r for r in results if "success" in r]),
            "total_charts": len(chart_types),
            "results": results
        }

# 創建默認實例
default_data_visualizer = DataVisualizer()
