from fastapi import FastAPI
import asterisk.manager # pip install pyst2
import sys


app = FastAPI()

@app.get("/healthcheck")
async def healthcheck(event):
    def handle_event(event, manager):
        print ("Recieved event: %s" % event.name)
        if event.headers.get('Channel'):
            channel = event.headers['Channel'].split('/')[1].split('-')[0]
            return event.headers['CallerIDNum']#(f"\n channel:{channel}"
                #f"\n\t CallerIDNum: {event.headers['CallerIDNum']} "
                #f"\n\t CallerIDName: {event.headers['CallerIDName']} "
                #f"\n\t ConnectedLineName: {event.headers['ConnectedLineName']} "
                #f"\n\t ConnectedLineNum: {event.headers['ConnectedLineNum']} "
            #)
    manager = asterisk.manager.Manager()
    
    try:
        # connect to the manager
        try:
            manager.connect('172.31.16.81')
            manager.login('guruweb', 'myvi2021!')

            # register some callbacks
            #manager.register_event('Shutdown', handle_shutdown) # shutdown
            
            manager.register_event(
                'BridgeEnter', handle_event)
            
            #manager.register_event('*', handle_event)           # catch all

            # get a status report
            response = manager.status()
            #print(response.data)

            manager.message_thread.join()

        except asterisk.manager.ManagerSocketException as e:
            #print ("Error connecting to the manager: %s" % e)
            sys.exit(1)
        except asterisk.manager.ManagerAuthException as e:
            #print ("Error logging in to the manager: %s" % e)
            sys.exit(1)
        except asterisk.manager.ManagerException as e:
            #print ("Error: %s" % e)
            sys.exit(1)

    finally:
    # remember to clean up
        #print(dir(manager))
        manager.close()
        return {"status": "ok"}
