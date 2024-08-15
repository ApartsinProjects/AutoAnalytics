from fasthtml import FastHTML,Main,Form,Input,Button,serve,P,A,H1,Label,Select,Option,Table,Tr,Td,Th,Div
from fasthtml.common import *
from mngDB import MngDB



class MainPage:
    def __init__(self):
        self.mngDB=MngDB()
        self.users=None
        
    def enumerate_users(self):
        self.users=self.mngDB.store.fetchall("select * from users")
        for user in self.users: 
            user['org_info']=self.mngDB.get_obj("org",user["user_org_uid"])
        return self.users
        
    def selection_box(self): 
        self.enumerate_users()
        men=[{'display':f"user={u['user_name']} role={u['user_role']} org={u['org_info']['org_name']}","value":u['user_uid']} for u in self.users]
        return Label("Choose user", Select(*[Option(u['display'],value=u['value']) for u in men],name="uuid"))
    
    def form(self):
        return Form(self.selection_box(),Button("GO",type="submit"),action="/user_info", method="GET")
    
    def user_info(self,user_uid):
        user_info,org_info, tasks=self.mngDB.describe_user(user_uid)
        return self.user_head(user_info),self.org_head(org_info),self.task_head(tasks),self.kpi_head(user_uid)
           
    def user_head(self, ui): return H1("User Information"), Table(Tr(Th("Name"),Th("Role")),Tr(Td(ui['user_name']),Td(ui['user_role'])),border="1"), P()
    def org_head(self,oi): return H1("Org Information"), Table(Tr(Th("Field"),Th("Value")),
                                        Tr(Td("Name"),Td(oi['org_name'])),
                                        Tr(Td("Description"),Td(oi['org_descr'])),
                                        Tr(Td("Data Source"),Td(oi['org_data_app'])),
                                        Tr(Td("Connection"),Td(oi['org_conn_str'])),
                                        Tr(Td("Data Summary[AI]"),Td(oi['data_summary'])),
                                        Tr(Td("Data gaps[AI]"),Td(oi['data_gaps'])),
                                        Tr(Td("Data entities[AI]"),Td(str(oi['data_entities']))),
                                        Tr(Td("Data relations[AI]"),Td(str(oi['data_relations']))),
                                        border="1"),P()
                                        
    def task_head(self,tasks): 
        print(tasks[0])
        tasks_rows=[Tr(Td(t['task_responsibility']),Td(t['task_name'])) for t in tasks]
        return H1("User Tasks[AI]"),Table(Tr(Th("Task group[AI]"),Th("Task[AI]")),
                                                   *tasks_rows,
                                                   border=1),P()
    
    def kpi_head(self,user_uid):
        kpis=self.mngDB.store.fetchall(f"select kpis.* from kpis join tasks on kpis.kpi_task_uid=tasks.task_uid where tasks.task_user_uid='{user_uid}' and kpis.sql_passed='true'" )
        kpi_rows=[Tr(Td(k['kpi_name']),Td(k['kpi_description']),Td(A('query',href=f"/query/{k['kpi_uid']}"))) for k in kpis]
        return H1("KPIs[AI]"),Table(Tr(Th("KPI[AI]"),Th("Description[AI]"),Th("SQL Query[AI]")),*kpi_rows,border=1),P()
    
    def query(self, kpi_uid):
        kpi=self.mngDB.get_obj("kpi",kpi_uid)
        org=self.mngDB.store.fetchall(f"select orgs.* from orgs join users on orgs.org_uid=users.user_org_uid join tasks on users.user_uid=tasks.task_user_uid where tasks.task_uid='{kpi['kpi_task_uid']}'")[0]
        
        #return str(kpi)
        return self.kpi_header(kpi),self.res_head(kpi['sql_results_raw']),self.sql_head(kpi,org)
    
    def kpi_header(self,kpi): return  H1("[AI]:"+kpi['kpi_name']+f"(fetched on {kpi['sql_test_time']})"),H2("[AI]:"+kpi['kpi_description']) 
    
    def sql_head(self,kpi,org):
        return H1("[AI] SQL:"),Div(kpi['sql_stmt']),Div(H2("Data connection string"),org['org_conn_str']),P(),Button("Refresh")
    
    def res_head(self,sql_results):
        if len(sql_results)==0: return Div("empty")
        
        header_row=Tr(*[Td(k,style="font-weight:bold") for k in sql_results[0].keys()])
        data_rows=[]
        for r in sql_results:data_rows.append(Tr(*[Td(v) for v in r.values()]))
        return Table(header_row, *data_rows ,border=1),P()
    
app = FastHTML()    
mp=MainPage()


@app.get("/")
def home():return mp.form()

@app.get("/user_info")
def user_info(uuid:str):return mp.user_info(uuid)

@app.get("/query/{kpi_uid}")
def kpi_query(kpi_uid:str):return mp.query(kpi_uid)
 
serve()     
        
       