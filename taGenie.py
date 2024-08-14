from mngDB import MngDB
from schemeAnnotator import SchemeAnnotator
from taskGen import TaskGen
from kpiGen import KPIGen
from sqlGen import SQLGen
from sqlChecker import SQLChecker

fleet_user_info={"user_name":"John","user_role":"Fleet manager"}
fleet_org_info={"org_name":"Egged",
          "org_descr":"bus public transportation company",
          "org_conn_str":"dbname='acmebus' user='taskanalytics' password='leningrad' host='localhost' port='5432'",
          "org_data_app":"telematics solution"}

class TAGenie:
    def __init__(self): pass
    def generate_analytics(self,user_info, org_info):
        user_info=self.provision_user(user_info,org_info)
        self.prepare_schema(user_info['user_org_uid'])
        self.generate_tasks(user_info['user_uid'])
        self.generate_kpis(user_info['user_uid'])
        self.generate_queries(user_info['user_uid'])
        self.test_queries(user_info['user_uid'])
        
    def provision_user(self,user_info,org_info): return MngDB().create_or_update_user(user_info, org_info)
    def prepare_schema(self, org_uid): return SchemeAnnotator().prepare_schema(org_uid)
    def generate_tasks(self, user_uid): return TaskGen().generate_user_tasks(user_uid)
    def generate_kpis(self,user_uid): return KPIGen().generate_user_kpis(user_uid)
    def generate_queries(self, user_uid): return SQLGen().generate_kpis_sql(user_uid)
    def test_queries(self, user_uid): return SQLChecker().test_kpis(user_uid)
        
        