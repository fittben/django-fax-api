import main.utils.esl.ESL_py3 as ESL
from ..vars import FREESWITCH_IP_ADDRESS, FREESWITCH_PORT, FREESWITCH_PASSWORD
import os
import uuid


class FaxSimple:
    """Simplified fax sending without CDR pusher dependency"""
    
    def __init__(self, username, file_path, numbers):
        self.username = username
        self.file_path = file_path
        self.numbers = numbers
        self.numbers_list = self.numbers.split(',')
        self.uuid = str(uuid.uuid4())
        
    def execute(self):
        args = {
            'uuid': self.uuid,
            'details': []
        }
        
        con = ESL.ESLconnection(FREESWITCH_IP_ADDRESS, FREESWITCH_PORT, FREESWITCH_PASSWORD)
        
        if not con.connected():
            args['error'] = 'Failed to connect to FreeSWITCH'
            return args
            
        try:
            for number in self.numbers_list:
                # Generate UUID for this specific call
                core_uuid = con.api("create_uuid").getBody()
                
                # Build originate command
                str_cmd = self._build_originate_command(core_uuid, number)
                
                # Execute in background
                res = con.bgapi("originate", str_cmd)
                
                # Collect details
                detail = {
                    'cli': self.username,
                    'cld': number,
                    'file': os.path.basename(self.file_path),
                    'body': res.getBody(),
                    'event-name': res.getHeader("Event-Name"),
                    'job-uuid': core_uuid
                }
                
                args['details'].append(detail)
                
        except Exception as e:
            args['error'] = str(e)
            
        finally:
            con.disconnect()
            
        return args
    
    def _build_originate_command(self, core_uuid, number):
        """Build the originate command string"""
        params = [
            f"origination_uuid={core_uuid}",
            "ignore_early_media=true",
            "absolute_codec_string='PCMU,PCMA'",
            "fax_enable_t38=true",
            "fax_verbose=true",
            "fax_use_ecm=false",
            "fax_enable_t38_request=false",
            f"fax_ident={self.username}"
        ]
        
        param_string = ','.join(params)
        command = f"{{{param_string}}}sofia/gateway/{self.username}/{number} &txfax({self.file_path})"
        
        # Remove newlines for clean command
        return command.replace("\n", "")