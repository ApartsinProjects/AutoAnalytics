from mngDB import MngDB
from schemeAnnotator import SchemeAnnotator
from taskGen import TaskGen
from kpiGen import KPIGen
from sqlGen import SQLGen
from sqlChecker import SQLChecker
from userReport import UserReport
from visGen import VisGen
from insGen import InsightGen
from mngDB import MngDB
import logging

class TAGenie:
    def __init__(self):
        self.Phases={
                    "delete": self.delete_case,
                    "create":self.provision_user,
                     "schema":self.prepare_schema,
                     "tasks":self.generate_tasks,
                     "kpis":self.generate_kpis,
                     "sql":self.generate_queries,
                     "test":self.test_queries,
                     "report":self.print_user_report,
                     "debug":self.attempt_fix_sqls,
                     "insights": self.generate_insights,
                     "visuals":self.generate_visuals}
        
    def process(self,use_case,steps=["create","schema","tasks","sql","test","report","debug","report","insights","visuals"]):
        
        for s in steps:
            if s in ['create','delete']:
                self.Phases[s](use_case)
            else:
                user_obj=MngDB().find_user(use_case['user']['user_name']) 
                if user_obj: 
                    self.Phases[s](user_obj['user_uid'])
                else:
                    logging.info(f"can't find user {use_case['user']['user_name']}")
                    break
                
                
        logging.info(f"\n*********************************** done ****************************************************************************\n")
        
    def delete_case(self,use_case): 
        logging.info(f"\n============================ deleting case data=======================================================\n")
        return MngDB().delete_case_data(use_case['user']['user_name'])
    
    def provision_user(self,use_case): 
        logging.info(f"\n============================ starting provisioning of user and his org=======================================================\n")
        return MngDB().create_case(use_case['user'], use_case['org'])
    
    def generate_insights(self, user_uid):
        logging.info(f"\n============================ generating insights =======================================================\n")
        return InsightGen().derive_insights(user_uid)
    
    def prepare_schema(self, user_uid): 
        org_uid=MngDB().get_user(user_uid)["user_org_uid"]
        logging.info(f"\n============================ fetching and annotating DB scheme=======================================================\n")
        return SchemeAnnotator().prepare_schema(org_uid)
    
    def generate_tasks(self, user_uid): 
        logging.info(f"\n============================ generate user responsibilities and tasks =======================================================\n")
        return TaskGen().generate_user_tasks(user_uid)
    
    def generate_kpis(self,user_uid): 
        logging.info(f"\n============================ generating user KPIs =======================================================\n")
        return KPIGen().generate_user_kpis(user_uid)
    
    def generate_queries(self, user_uid): 
        #return SQLGen().generate_kpis_sql(user_uid)
        logging.info(f"\n============================ generating KPI SQL queries =======================================================\n")
        return SQLGen().generate_kpis_sql_raw(user_uid)
    
    def test_queries(self, user_uid): 
        logging.info(f"\n============================ testing KPI SQL queries =======================================================\n")
        return SQLChecker().test_kpis(user_uid)
    
    def print_user_report(self,user_uid):
        logging.info(f"\n============================ reporting KPI and data stats =======================================================\n")
        return  UserReport().print_user_stats(user_uid)
    
    def attempt_fix_sqls(self,user_uid):
        logging.info(f"\n============================ attempting to debug and fix queries =======================================================\n")
        return SQLGen().attempt_fix_sqls(user_uid)
    
    def generate_visuals(self,user_uid):
        logging.info(f"\n============================ generating visuals =======================================================\n")
        return VisGen().generate_user_visuals(user_uid)
        
        