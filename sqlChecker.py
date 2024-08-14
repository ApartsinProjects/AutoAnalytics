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
        user_org=self.mngDB.get_user_org(user_uid)
        
        self.tables=self.mngDB.get_org_tables(user_org['org_uid'])
        self.cols={table['table_uid']:self.mngDB.get_table_columns(table['table_uid']) for table in self.tables}
        
        org_kpis_uids=self.mngDB.get_user_kpis_ids(user_uid)
        self.remote.connect_str(user_org["org_conn_str"])
        for kpi_uid in org_kpis_uids:self.test_kpi(kpi_uid)
        
    def test_kpi(self,kpi_uid):
        kpi_info=self.mngDB.get_obj("kpi",kpi_uid)
        stmt=kpi_info['sql_stmt'].replace('@periodStart',self.period['testStartPeriod']).replace('@periodEnd',self.period['testEndPeriod'])
        src_res_json,decoded_res_json,key_map=None,None,None
        try:
            src_res=self.remote.fetchall(stmt,)
            if len(src_res)>10: src_res=src_res[:10]
            decoded_res,key_map=self.encode_results_aliases(src_res) if src_res else None
            src_res_json,decoded_res_json=json.dumps(src_res,default=str),json.dumps(decoded_res,default=str)
        except:
            pass
        finally:
            self.save_results(kpi_uid,src_res_json,decoded_res_json,key_map)
            
    def save_results(self, kpi_uid, src_json,decoded_json,key_map):
        kpi_info={'kpi_uid':kpi_uid,
                  "sql_passed":"true" if decoded_json else "false",
                  "sql_test_time":f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"}
        if decoded_json:
            kpi_info["sql_results"]=sql_text(decoded_json)
            kpi_info["sql_results_raw"]=sql_text(src_json)
            kpi_info['sql_res_cols_raw']=sql_text(json.dumps(list(key_map.keys())))
            kpi_info['sql_res_cols_alias']=sql_text(json.dumps(list(key_map.values())))
            kpi_info['sql_col_map']=sql_text(json.dumps(key_map))
        self.mngDB.update_obj("kpi",kpi_info)
            
    def map_keys(self,rec):
        all_keys=dict(zip(rec.keys(),rec.keys()))
        for table in self.tables:
            for c in self.cols[table['table_uid']]:
                if c['col_name'].lower() in all_keys: all_keys[c['col_name'].lower()]=c['col_alias']
        return all_keys
                        
    def encode_results_aliases(self,result_set):
        key_map=self.map_keys(result_set[0])
        return [remap_dict(dict(rec.items()),key_map) for rec in result_set],key_map
        
        