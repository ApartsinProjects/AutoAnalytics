from mngDB import MngDB
import json

def find_col_alias(col_name, col_list):
    for c in col_list: 
        if c["col_name"].lower()==col_name.lower(): return c['col_alias']
    return "[unknown]"

class SchemePrompt:
    def __init__(self):
        self.mngDB=MngDB()
        
    #for enriching teh schema
    def get_schema_prompt(self, org_uid):
        tables=self.mngDB.get_org_tables(org_uid)
        return ";".join([self.get_table_prompt(table,org_uid) for table in tables])
    
    def get_pkeys_prompt(self,pkey):return f"primary key columns:{str(pkey.get('constrained_columns'))}"
    
    def get_fkeys_prompt(self,fkeys):
            fkey_prompts=[]
            for fkey in fkeys:
                fkey_prompts.append(f"foreign key col:{str(fkey['constrained_columns'])} referred to table cols:{fkey['referred_columns']} of referred table:'{fkey['referred_table']}'")
            return ";".join(fkey_prompts)
        
    def get_table_prompt(self, table,org_uid):
        cols=self.mngDB.get_table_columns(table['table_uid'])
        column_prompt=",".join([f"`{c['col_name']}` of type {c['col_type']} with sample values:{c['col_sample_vals']}" for c in cols])
        return f"table:`{table['table_name']}` {self.get_pkeys_prompt(table['table_pkeys'])} {self.get_fkeys_prompt(table['table_fkeys'])} with columns:[{column_prompt}]"
    
    #enriched scheme for KPIs generation
    def get_rich_schema_prompt(self,org_uid):
        tables=self.mngDB.get_org_tables(org_uid)
        return ";".join([self.get_rich_table_prompt(table) for table in tables])
    
    def get_annotated_schema_prompt(self,org_uid):
        tables=self.mngDB.get_org_tables(org_uid)
        return ";".join([self.get_annotated_table_prompt(table) for table in tables])
    
    def get_annotated_table_prompt(self, table):
        cols=self.mngDB.get_table_columns(table['table_uid'])
        column_prompt=",".join([f"`{c['col_name']}` of type {c['col_type']} with sample values:{c['col_sample_vals']} and description:{c['col_desc']}" for c in cols])
        return f"table:`{table['table_name']}` represents {table['table_desc']} {self.get_pkeys_prompt(table['table_pkeys'])} {self.get_fkeys_prompt(table['table_fkeys'])} with columns:[{column_prompt}]"
    
    def get_rich_table_prompt(self, table):
        cols=self.mngDB.get_table_columns(table['table_uid'])
        column_prompt=",".join([f"{c['col_alias']} represents:{c['col_desc']}" for c in cols])
        return f"table:'{table['table_alias']}, table description:{table['table_desc']}' with columns:[{column_prompt}]"
    
    def get_summary_prompt(self,org_uid):
        org=self.mngDB.get_obj("org",org_uid)
        return f"{org['data_summary']};{org['data_gaps']}"