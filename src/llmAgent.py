agent_cfg={'model':"gpt-4o-mini",
           #'model': "gpt-3.5-turbo",
           #'model': "gpt-4o-2024-08-06",
           'temperature':0,
           "key":"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",
           }

from openai import OpenAI
import copy,logging

class LLMAgent:
    
    def __init__(self,cfg=agent_cfg,prompt_lib=None):
        self.cfg=copy.deepcopy(cfg)
        self.client=OpenAI(api_key=self.cfg["key"])
        self.prompt_lib=prompt_lib

    def struct_query(self, sys_msg,user_msg,fmt_class):
        completion = self.client.beta.chat.completions.parse(
            model=self.cfg['model'],temperature=self.cfg['temperature'],
            messages=[{"role": "system", "content": sys_msg},{"role": "user", "content": user_msg}],
            response_format=fmt_class)
        logging.info(f"llm retunr={completion.choices[0].message.parsed}")
        return completion.choices[0].message.parsed
    
    