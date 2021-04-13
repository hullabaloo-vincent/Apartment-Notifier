import logging
import os

from flask import Flask, render_template
from craigslist import CraigslistHousing
from twilio.rest import Client 

app = Flask(__name__)
app.config.from_json("config.json")


@app.route('/')
def root():
    return render_template(
        'index.html')

@app.route('/get_new_listings', methods=['GET', 'POST'])
def new_listing():
    cl_h = CraigslistHousing(site='maine', category='apa',
                         filters={'max_price': 1200, 'private_room': True, 'dogs_ok': True})
    craigslist_items = {
        'items': []
    }
    m_size = 0
    headers = {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:61.0) Gecko/20100101 Firefox/61.0'}
    sms_body = "Found the following apartments from Craigslist:"
    for result in cl_h.get_results(sort_by='newest', geotagged=True):
        if result['has_image'] and m_size <= 5:
            sms_body = sms_body + "\nApartment in " + str(result['where']) +  " for " + str(result['price']) + " : " + str(result['url'])
            craigslist_items['items'].append({
                'title':str(result['name']),
                'price':str(result['price']),
                'where':str(result['where']),
                'url':str(result['url'])
            })
            m_size +=1
        else:
            break
    
    account_sid = app.config["TWILIO_CLIENT_ID"]
    auth_token = app.config["TWILIO_TOKEN"]
    client = Client(account_sid, auth_token) 
    message = client.messages.create(  
        messaging_service_sid=app.config["MESSAGE_SERVICE_ID"], 
        body=sms_body,      
        to=app.config["PERSONAL_NUMBER"] 
    ) 
    return craigslist_items

@app.errorhandler(500)
def server_error(e):
    logging.exception('Yikes! That was not supposed to happen.')
    return """
    An internal error occurred: <pre>{}</pre>
    """.format(e), 500


if __name__ == '__main__':
    server_port = os.environ.get('PORT', '8080')
    app.run(debug=True, port=server_port, host='0.0.0.0')