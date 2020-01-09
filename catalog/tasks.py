import socket
from ssh2.session import Session
import password_generator
import string
import random
import names
from randomword import RandomWord

from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.utils.crypto import get_random_string

from celery import shared_task, task, current_task
from Library_Rework.celery import app
from celery.utils.log import logger
from celery.schedules import crontab
from Library_Rework.celery import app as celery_app

from .models import Genre, Language, Author
from .kwargs_example import create_new_whm_account

@shared_task
def create_random_user_accounts(total):
    for num in range(total):
        r = RandomWord()
        username = 'user_{}'.format(r.get()['word'])
        email = '{}@example.com'.format(username)
        password = get_random_string(15)
        User.objects.create_user(username=username, email=email, password=password)
    return '{} random users created with success!'.format(total)

# @app.task
@shared_task
def send_emails_to_all_usesr():

    user_list_email = [user_lists.email for user_lists in User.objects.all()]
    send_mail_task(f'Hello and greetings!', user_list_email)

    return 'All Emails Sent!'

@shared_task
def send_mail_task(html_message, recipient_list):
    send_mail(
        subject='Automatic Celery Task Response!',
        message='Hello Everyone!',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=recipient_list,
        fail_silently=False,
        html_message=html_message
    )
    return f'Mail Sent!'

@shared_task
def create_new_author():
    first_name = names.get_first_name()
    last_name = names.get_last_name()
    full_name = f'{last_name}, {first_name}'

    all_full_names = [names.get_name() for names in Author.objects.all()]
    if (full_name in all_full_names):
        print(f'Author already exists: {full_name}')
        return f'Author {full_name} already exists! Aborting!'

    else:
        Author.objects.create(first_name=first_name, last_name=last_name)
        text = f'A new author was created: {full_name}'
        send_mail_task(text, ['your_email@gmail.com', ])
        return f'Author {full_name} created!'

@shared_task
def create_random_genres(total):
    total_items_created = 0
    for num in range(total):
        r = RandomWord()
        genre_name = r.get()['word']

        if Genre.objects.filter(name=genre_name).exists():
            print('Genre Exists!')
        else:
            Genre.objects.create(name=genre_name)
            total_items_created += 1
            print(f'Genre {genre_name} created')

        print('Success!')
        print(r.get()['word'])
    message_success = f'A total of {total_items_created} Genres were created! Some genres might not be created as duplicate!' \
                      f'Greetings!'
    send_mail_task(message_success, ['your_email@gmail.com'])

    return f'{total_items_created} genres created'

@shared_task
def create_random_languages(total):
    total_items_created = 0
    for num in range(total):
        r = RandomWord()
        language_name = r.get()['word']

        if Language.objects.filter(name=language_name).exists():
            print('Language Exists!')
        else:
            Language.objects.create(name=language_name)
            total_items_created += 1
            print(f'Language {language_name} created')

        print('Success!')
        print(r.get()['word'])
    message_success = f'A total of {total_items_created} Languages were created! Some genres might not be created as duplicate!' \
                      f'Greetings!'
    send_mail_task(message_success, ['your_email@gmail.com'])

    return f'{total_items_created} languages created'

# This function would be used in 'create_new_whm_account'
# It would be only used if there is an existing account on the server
# It would add three characters to the desired account name
def generate_new_account_name(account_name):
    for i in range(3):
        random_letter = random.choice(string.ascii_letters)
        print(f'Adding {random_letter} to the username')
        account_name += random_letter

    return account_name

@shared_task
def create_new_whm_account(domain_name):

    # generate password
    new_pass = password_generator.generate(length=15)

    # open connection
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(('your_hostname', 'your port number remove brackets'))

    session = Session()
    session.startup(sock)
    session.userauth_password('username', 'your_password')

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

            message = (f'Account created! Here are the details:'
                  f'username = {username_whm_account} '
                  f'password = {new_pass} '
                  f'domain name = {domain_name} ')

            send_mail_task(message, ['your_email@gmail.com'])
