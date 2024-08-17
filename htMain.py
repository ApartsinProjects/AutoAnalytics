from fasthtml import FastHTML,Main,Form,Input,Button,serve,P,A,H1,Label,Select,Option,Table,Tr,Td,Th,Div,Br,Link
from fasthtml.common import *
from mngDB import MngDB



class MainPage:
    def __init__(self):
        self.mngDB=MngDB()
        self.users=None
        
    def user_list(self):
        users=self.mngDB.store.fetchall("select users.*, orgs.* from users left join orgs on users.user_org_uid=orgs.org_uid")
        return H1("Demo Users"),Table(Tr(Th("user name"),Th("role"),Th("org name")), \
                    *[Tr(Td(A(u['user_name'], href=f"/user_info/{u['user_uid']}")),Td(u['user_role']), Td(u['org_name'])) for u in users], border=1), Button("New User")
        
    def user_info(self, user_uid):
        
        user_info,org_info, tasks=self.mngDB.describe_user(user_uid)
        return self.user_params(user_info), self.org_params(org_info), H1(
            Table(Tr(Td(A("AI Data Annotations",href=f"/schema/{user_info['user_org_uid']}")), Td(A("AI-generated KPIs",href=f"/user_kpis/{user_uid}")))),border=0)
    
    def user_params(self, ui): return H1("User Details"),\
        Table(Tr(Th("Name"),Th("Role")),
                 Tr(Td(ui['user_name']),
                    Td(ui['user_role'],A("Edit",href=f"."),Br(),A(H3("AI-generated tasks"),href=f"/tasks/{ui['user_uid']}"))) ,border="1"), P()
        
    def org_params(self,oi): return H1("Organization Details"),\
                                        Table(Tr(Th("Field"),Th("Value")),
                                        Tr(Td("Org name"),Td(oi['org_name'],A("Edit",href="."))),
                                        Tr(Td("Org description"),Td(oi['org_descr'],A("Edit",href="."))),
                                        Tr(Td("Org data source type"),Td(oi['org_data_app'],A("Edit", href="."))),
                                        Tr(Td("Data connection info"),Td(oi['org_conn_str'],A("Edit",href="."))),
                                        border=1)
        
    def user_kpis(self,user_uid):
        user_info,org_info, tasks=self.mngDB.describe_user(user_uid)
        return self.kpi_list(user_uid)
    
    
    def data_annotations(self,org_uid): 
        oi=self.mngDB.get_obj("org",org_uid)
        return Div(H2("Data Summary[AI]"),\
        Table(Tr(Th("Field"),Th("Value")),
            Tr(Td("Summary"),Td(oi['data_summary'],A("Regenerate",href="."),A("Edit",href="."))),
            Tr(Td("Gaps"),Td(oi['data_gaps'],A("Regenerate",href="."),A("Edit",href="."))),
            Tr(Td("Entities"),Td(str(oi['data_entities']),A("Regenerate",href="."),A("Edit",href="."))),
            Tr(Td("Relations"),Td(str(oi['data_relations']),A("Regenerate",href="."),A("Edit",href="."))),
            border="1"),P(),Button("Regenerate All"))
                                        
    def task_list(self,user_uid): 
        user=self.mngDB.get_obj("user",user_uid)
        tasks=self.mngDB.store.fetchall(f"select * from tasks where tasks.task_user_uid='{user_uid}'")
        tasks_rows=[Tr(Td(t['task_responsibility']),Td(t['task_name']),Td(A("Delete",href="."),Br(),A("Edit",href="."))) for t in tasks]
        return H1(f"AI-generated tasks for ",A(f"{user['user_name']}", href=f"/user_info/{user_uid}")), H2(f"{user['user_role']}"),Table(Tr(Th("Task group"),Th("Task"),Th("Actions")),
                                                   *tasks_rows,
                                                   border=1),Table(Tr(Td(Button("Regenerate All")),Td(Button("Manually add tasks")),Td(Button("Suggest more tasks")))), P()
        
    def schema_view(self,org_uid): 
        oi=self.mngDB.get_obj("org",org_uid)
        return H1(f"AI-generated annotation for ",A(f"'{oi['org_name']}'",href="/"), "data"),self.data_annotations(org_uid),self.table_list(org_uid)
        
    def table_list(self,org_uid):
        tables=self.mngDB.store.fetchall(f"select * from tables where table_org_uid='{org_uid}'")
        return  H2("Tables Annotations[AI]"), *[self.table_info(table)  for table in tables]
    
    def columns_view(self,table_uid):
        table=self.mngDB.get_obj("table",table_uid)
        cols=self.mngDB.store.fetchall(f"select * from cols where col_table_uid='{table_uid}'")
        return H1(f"Table [{table['table_name']}] annotations:",Button("RegenerateAll)")), \
            Table(Tr(Th("Name"),Th("Type"),Th("Sample Values"),Th("Alias[AI]"),Th("Description[AI]"),Th("Units[AI]"),Th("Reasoning[AI]"),Th("Action")),
            *[self.column_info(col) for col in cols], border=1)
            
    def column_info(self, ci):return Tr(Td(ci['col_name']),Td(ci['col_type']),Td(ci['col_sample_vals']),
                  Td(ci['col_alias']),Td(ci['col_desc']),Td(ci['col_units']),Td(ci['col_desc_justification']),Td(A("Regenerate",href="."),Br(),A("Edit",href=".")))
        
    def table_info(self, ti):
        return Div(H4(f"Table:[{ti['table_name']}] Annotations and ",A("Columns",href=f"/columns/{ti['table_uid']}")),
            Table(Tr(Th("Field"),Th("Value")),
            Tr(Td("Alias"),Td(ti['table_alias'],A("Edit",href="."),A("Regenerate"))),      
            Tr(Td("Description"),Td(ti['table_desc'],A("Edit",href="."),A("Regenerate"))),
            Tr(Td("Reasoning"),Td(ti['table_desc_justification'],A("Edit",href="."),A("Regenerate"))),      
            Tr(Td("Primary keys"),Td(str(ti['table_pkeys']),A("Edit",href="."))),      
            Tr(Td("Foreign keys"),Td(str(ti['table_fkeys']),A("Edit",href="."))),                                                                         
            border=1),P(),Button("Regenerate All"))

    def kpi_list(self,user_uid):
        ui=self.mngDB.get_obj("user",user_uid)
        kpis=self.mngDB.store.fetchall(f"select kpis.*, tasks.task_name from kpis join tasks on kpis.kpi_task_uid=tasks.task_uid where tasks.task_user_uid='{user_uid}' and kpis.sql_passed='true'" )
        kpi_rows=[Tr(Td(A(k['kpi_name'],href=f"/query/{k['kpi_uid']}")),Td(k['task_name']),Td(k['kpi_description']),
                     Td(A('Delete',href=f"/query/{k['kpi_uid']}"),Br(),A('More like this',href=f"/query/{k['kpi_uid']}"))) for k in kpis]
        return Div(H1("AI-generated KPIs for ",A(ui['user_name'],href=f"/user_info/{user_uid}")),Table(Tr(Th("KPI"),Th("Task"),Th("Description"),Th("Action")),*kpi_rows,border=1),P(),Button("Regenerate All"))
    
    def query(self, kpi_uid):
        kpi=self.mngDB.get_obj("kpi",kpi_uid)
        org=self.mngDB.store.fetchall(f"select orgs.* from orgs join users on orgs.org_uid=users.user_org_uid join tasks on users.user_uid=tasks.task_user_uid where tasks.task_uid='{kpi['kpi_task_uid']}'")[0]
        
        #return str(kpi)
        return self.kpi_header(kpi),self.res_head(kpi['sql_results_raw']),self.sql_head(kpi,org)
    
    def kpi_header(self,kpi): return  H1(""+kpi['kpi_name']+f"(fetched on {kpi['sql_test_time']})"),H4(kpi['kpi_description']) 
    
    def sql_head(self,kpi,org):
        return H1("[AI] SQL:"),Div(kpi['sql_stmt']),Div(H2("Data connection string"),org['org_conn_str']),P(),Button("Refresh")
    
    def res_head(self,sql_results):
        if len(sql_results)==0: return Div("empty")
        
        header_row=Tr(*[Td(k,style="font-weight:bold") for k in sql_results[0].keys()])
        data_rows=[]
        for r in sql_results:data_rows.append(Tr(*[Td(v) for v in r.values()]))
        return Table(header_row, *data_rows ,border=1),P()
    


#app = FastHTML(hdrs=(Link(rel='stylesheet', href='users.css', type='text/css')))    
app, rt = fast_app(
    pico=False,
    hdrs=(
        Link(rel='stylesheet', href='assets/normalize.min.css', type='text/css'),
        Link(rel='stylesheet', href='assets/sakura.css', type='text/css'),
        Link(rel='stylesheet', href='/users.css', type='text/css'),
        Link(rel='stylesheet', href='/user.css', type='text/css')
))   




mp=MainPage()



@app.get("/")
def home():return mp.user_list()

@app.get("/user_info/{user_uid}")
def user_info(user_uid:str):return mp.user_info(user_uid)

@app.get("/user_kpis/{user_uid}")
def user_kpis(user_uid:str):return mp.user_kpis(user_uid)

@app.get("/query/{kpi_uid}")
def kpi_query(kpi_uid:str):return mp.query(kpi_uid)

@app.get("/schema/{org_uid}")
def schema_annotation(org_uid:str):return mp.schema_view(org_uid)

@app.get("/columns/{table_uid}")
def columns_annotation(table_uid:str):return mp.columns_view(table_uid)

@app.get("/tasks/{user_uid}")
def task_list(user_uid:str):return mp.task_list(user_uid)


 
serve()     
        
       