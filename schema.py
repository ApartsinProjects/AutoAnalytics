from pydantic import BaseModel

class ColumnMetadata(BaseModel):
    column_name: str 
    column_type: str
    column_units: str
    column_description: str
    column_sample_values: list[str]
    def __str__(self): return f"column name:{self.column_name} of type:{self.column_type} description:{self.column_description}"
    def ddl(self): return f"{self.column_name} {self.column_type}"
    
class TableMetadata(BaseModel):
    table_name: str
    table_columns: list[ColumnMetadata]
    table_description: str
    def __str__(self):
        cols_str=",".join([str(c) for c in self.table_columns])
        return f"table name:{self.table_name} table description:{self.table_description} table columns:({cols_str})"
    
class DataScheme(BaseModel):
    tables:list[TableMetadata]
    def __str__(self): return ";".join([str(t) for t in self.tables])
    def display(self):
        for t in self.tables:
            print(f"\n>>>> Table name: {t.table_name} , Description:{t.table_description}")
            print(f"\t{'name':20}\t{'type':10}\t{'units':10}\tdescription")
            for c in t.table_columns:print(f"\t{c.column_name:20}\t{c.column_type:10}\t{c.column_units:10}\t{c.column_description}")