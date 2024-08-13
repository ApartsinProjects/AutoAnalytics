from mngDB import MngDB

class SchemePrompt:
    def __init__(self):
        self.mngDB=MngDB()
        
    def get_schema_prompt(self, org_uid):
        tables=self.mngDB.get_org_tables(org_uid)
        return ";".join([self.get_table_prompt(table,org_uid) for table in tables])
    
    def get_table_prompt(self, table,org_uid):
        cols=self.mngDB.get_table_columns(table['table_uid'])
        column_prompt=",".join([f"{c['col_name']} of type {c['col_type']} with sample values:{c['col_sample_vals']}" for c in cols])
        return f"table:'{table['table_name']}' with columns:[{column_prompt}]"