import socket
from ssh2.session import Session
import password_generator
import string
import random
import names

def generate_new_account_name(account_name):
    for i in range(3):
        random_letter = random.choice(string.ascii_letters)
        print(f'Adding {random_letter} to the username')
        account_name += random_letter

    return account_name

def create_new_whm_account(domain_name):

    # generate password
    new_pass = password_generator.generate(length=15)

    # open connection
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(('your_hostname', 'port_number_integer_remove_brackets'))

    session = Session()
    session.startup(sock)
    session.userauth_password('root', 'your_password')

    chanel = session.open_session()

    # form a 8-letter username
    username_whm_account = ''
    for char_letter in domain_name:
        if char_letter.isalpha():
            username_whm_account += char_letter

    username_whm_account = username_whm_account[:8]

    # check if username and domain name already exist on the server
    chanel.execute(f'cd /var/cpanel/users; grep -r {domain_name}; grep -r {username_whm_account}')

    size, data = chanel.read()
    while(size > 0):
        # convert byte output to string
        datada = str(data.decode('ascii'))
        print(datada)
        size, data = chanel.read()

        if (f'DNS={domain_name}' in datada):
            print(f'Domain name {domain_name} already exists! Account creation failed! Aborting...')
            return 0

        else:
            while(f'USER={username_whm_account}' in datada):
                print(f'Account name already exists! Creating new username!')
                username_whm_account = generate_new_account_name(username_whm_account)

            print(username_whm_account)

            chanel.close()
            chanel = session.open_session()
            chanel.execute(f'whmapi1 createacct username={username_whm_account} domain={domain_name} password={new_pass}')

            print(f'Account created! Here are the details:'
                  f'username = {username_whm_account} '
                  f'password = {new_pass} '
                  f'domain name = {domain_name} ')

            # username_whm_account = pre_username_whm_account
        # else:
        #     chanel.close()
        #     chanel = session.open_session()
        #     chanel.execute(f'whmapi1 createacct username={username_whm_account} domain={domain_name} password={new_pass}')
        #
        #     print(f'Account created! Here are the details:'
        #           f'username = {username_whm_account} '
        #           f'password = {new_pass} '
        #           f'domain name = {domain_name} ')

# create_new_whm_account('accountedeeeded.remote.com')

from randomword import RandomWord

rand_title = RandomWord()
rand_title = rand_title.get()['word']
print(rand_title.capitalize())


