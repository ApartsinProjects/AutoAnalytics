from mngDB import MngDB

class SchemePrompt:
    def __init__(self):
        self.mngDB=MngDB()
        
    #for enriching teh schema
    def get_schema_prompt(self, org_uid):
        tables=self.mngDB.get_org_tables(org_uid)
        return ";".join([self.get_table_prompt(table,org_uid) for table in tables])
    
    def get_table_prompt(self, table,org_uid):
        cols=self.mngDB.get_table_columns(table['table_uid'])
        column_prompt=",".join([f"{c['col_name']} of type {c['col_type']} with sample values:{c['col_sample_vals']}" for c in cols])
        return f"table:'{table['table_name']}' with columns:[{column_prompt}]"
    
    #enriched scheme for KPIs generation
    def get_rich_schema_prompt(self,org_uid):
        tables=self.mngDB.get_org_tables(org_uid)
        return ";".join([self.get_rich_table_prompt(table,org_uid) for table in tables])
    
    def get_rich_table_prompt(self, table,org_uid):
        cols=self.mngDB.get_table_columns(table['table_uid'])
        column_prompt=",".join([f"{c['col_alias']} represents:{c['col_desc']}" for c in cols])
        return f"table:'{table['table_alias']}, table description:{table['table_desc']}' with columns:[{column_prompt}]"
    
    #enriched but with original names for SQL generation
    def get_annotated_schema_prompt(self,org_uid):
        tables=self.mngDB.get_org_tables(org_uid)
        return ";".join([self.get_annotated_table_prompt(table,org_uid) for table in tables])
    
    def get_annotated_table_prompt(self, table,org_uid):
        cols=self.mngDB.get_table_columns(table['table_uid'])
        column_prompt=",".join([ self.get_annotated_column_prompt(c) for c in cols])
        return f"table:'{table['table_alias']} table description:{table['table_desc']}' with columns:[{column_prompt}]"
    
    #TBD add values information
    def get_annotated_column_prompt(self,c):
        return f"{c['col_alias']} of type {c['col_type']} with description:'{c['col_desc']}' sample values:'{c['col_sample_vals']}'"
    
    def get_summary_prompt(self,org_uid):
        org=self.mngDB.get_obj("org",org_uid)
        return f"{org['data_summary']};{org['data_gaps']}"