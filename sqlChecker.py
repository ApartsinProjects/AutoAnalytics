from mngDB import MngDB,sql_text
from dataSource import DataSource
from datetime import datetime
import copy,json

def remap_dict(d,key_map): return {key_map[k]:v for k,v in d.items()}

class SQLChecker:
    def __init__(self):
        self.mngDB=MngDB()
        self.remote=DataSource()
        self.period={'testStartPeriod':f"'{datetime(1, 1, 1, 0, 0).strftime('%Y-%m-%d %H:%M:%S')}'",
                    "testEndPeriod":f"'{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}'"}
        self.tables=None
        self.cols=None
        
    def test_kpis(self, user_uid):
        self.prepare_test_round(user_uid)
        org_kpis_uids=self.mngDB.get_user_kpis_ids(user_uid)
        for kpi_uid in org_kpis_uids:self.test_kpi(kpi_uid)
        
    def prepare_test_round(self,user_uid):
        user_org=self.mngDB.get_user_org(user_uid)
        self.tables=self.mngDB.get_org_tables(user_org['org_uid'])
        self.cols={table['table_uid']:self.mngDB.get_table_columns(table['table_uid']) for table in self.tables}
        self.remote.connect_str(user_org["org_conn_str"])
        return self
        
    def decode_results(self,src_res):
        if src_res:
            if len(src_res)>10: src_res=src_res[:10]
            decoded_res,key_map=self.encode_results_aliases(src_res) 
            return json.dumps(src_res,default=str),json.dumps(decoded_res,default=str),key_map
        else:
            return None,None,None
        
    def test_kpi(self,kpi_uid):
        kpi_info=self.mngDB.get_obj("kpi",kpi_uid)
        stmt,src_res,error=self.test_kpi_info(kpi_info)
        self.save_results(stmt,kpi_uid,src_res,error)
        
    def test_kpi_info(self,kpi_info):
        stmt=kpi_info['sql_stmt'].replace('@periodStart',self.period['testStartPeriod']).replace('@periodEnd',self.period['testEndPeriod'])
        src_res,error=self.remote.fetchall_with_diagnostics(stmt)
        return stmt,src_res,error
        
    def append_decoded(self,kpi_info,src_res):
        src_res_json,decoded_res_json,key_map=self.decode_results(src_res) 
        if decoded_res_json: 
            kpi_info["sql_passed"]="true" 
            kpi_info["sql_results"]=sql_text(decoded_res_json)
            kpi_info["sql_results_raw"]=sql_text(src_res_json)
            kpi_info['sql_res_cols_raw']=sql_text(json.dumps(list(key_map.keys())))
            kpi_info['sql_res_cols_alias']=sql_text(json.dumps(list(key_map.values())))
            kpi_info['sql_col_map']=sql_text(json.dumps(key_map))
        return kpi_info
            
    def save_results(self, stmt,kpi_uid, src_res,error):
        kpi_info={'kpi_uid':kpi_uid,"sql_passed":"false",
                  "sql_test_time":f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                  'sql_test_stmt':sql_text(stmt),'sql_error':sql_text(error) if error else "OK"}
        self.mngDB.update_obj("kpi",self.append_decoded(kpi_info,src_res))
            
    def map_keys(self,rec):
        all_keys=dict(zip(rec.keys(),rec.keys()))
        for table in self.tables:
            for c in self.cols[table['table_uid']]:
                if c['col_name'].lower() in all_keys: all_keys[c['col_name'].lower()]=c['col_alias']
        return all_keys
                        
    def encode_results_aliases(self,result_set):
        key_map=self.map_keys(result_set[0])
        return [remap_dict(dict(rec.items()),key_map) for rec in result_set],key_map
        
        