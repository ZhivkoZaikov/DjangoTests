from __future__ import absolute_import, unicode_literals

import datetime
import uuid

from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse

from . import validators

#celery!
# from __future__ import absolute_import, unicode_literals

from django.db import models  # noqa


class Widget(models.Model):
    name = models.CharField(max_length=140)
#celery!

class Genre(models.Model):
    name = models.CharField(max_length=200, help_text='Enter a book genre (e.g. Science Fiction)', unique=True)
    image = models.ImageField(upload_to='images/genres', null=True, blank=True)
    view_count = models.IntegerField('View Count', default=0)
    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('genre-detail', args=[str(self.id)])

class Language(models.Model):
    name = models.CharField(max_length=50,
                            help_text='Enter the book language(e.g. Spanish, English, Chinese, etc)', unique=True)
    view_count = models.IntegerField('View Count', default=0)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Language'

    def get_absolute_url(self):
        return reverse('language-detail', args=[str(self.id)])

class Author(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    date_of_birth = models.DateField(null=True, blank=True, validators=[validators.validate_date_not_in_future, ])
    # set 'Died' as a verbose name
    date_of_death = models.DateField('Died', null=True, blank=True, validators=[validators.validate_date_not_in_future, ])
    image = models.ImageField(upload_to='images/authors/', null=True, blank=True)
    about_the_author = models.TextField(max_length=1000, null=True, blank=True)
    view_count = models.IntegerField('View Count', default=0)

    class Meta:
        ordering = ['last_name', 'first_name']
        unique_together = ('first_name', 'last_name', )

    def get_absolute_url(self):
        return reverse('author-detail', args=[str(self.id)])

    def __str__(self):
        return f'{self.first_name}, {self.last_name}'

    def get_name(self):
        return f'{self.last_name}, {self.first_name}'

class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.ForeignKey('Author', on_delete=models.SET_NULL, null=True)
    summary = models.TextField(default='', max_length=1000, help_text='Enter a brief description of the book')
    isbn = models.CharField('ISBN', null=True, blank=True, max_length=13, help_text='13 characters <a href="https://www.isbn-international.org/content/what-isbn" target="_blank">ISBN number</a>')
    genre = models.ManyToManyField(Genre, help_text='Select a genre for this book', blank=True)
    language = models.ForeignKey('Language', on_delete=models.SET_NULL, null=True)
    date_added = models.DateField(null=True, blank=True, validators=[validators.validate_date_not_in_future, ])

    published = models.DateField(null=True, blank=True, validators=[validators.validate_date_not_in_future, ])
    copies = models.IntegerField()
    loaned_copies = models.IntegerField()
    available_copies = models.IntegerField()
    image = models.ImageField(upload_to='images/', null=True, blank=True)
    view_count = models.IntegerField('View Count', default=0)

    def display_genre(self):
        return ', '.join([genre.name for genre in self.genre.all()[:3]])

    # customize the column title by adding short_description attribute to the callable
    display_genre.short_description = 'Genre'

    # def latest_books(self):
    #     # p = self.objects.all().order_by('-date_added')[:3]
    #     return ', '.join(book.title for book in self.objects.all().order_by('-date_added'))

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('book-detail', args=[str(self.id)])

    class Meta:
        unique_together = ('title', 'author', )

class BookInstance(models.Model):
    book = models.ForeignKey('Book', on_delete=models.SET_NULL, null=True)
    imprint = models.CharField(max_length=200)
    due_back = models.DateField(null=True, blank=True)
    borrower = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    @property
    def is_overdue(self):
        # if self.due_back and date.today().strftime('%B %d %Y') > self.due_back.strftime('%B %d %Y'):
        if self.due_back and datetime.date.today() > self.due_back.date():
            return True
        return False

    # to print the verbose of 'status' in your website you would need to use get_status_display
    # it comes from get_variable_display and substitute variable with the actual variable
    LOAN_STATUS = (
        ('m', 'Maintenance'),
        ('o', 'On Loan' ),
        ('a', 'Available'),
        ('r', 'Reserved'),
    )

    status = models.CharField(max_length=1, choices=LOAN_STATUS, blank=True, default='m', help_text='Book availability')

    class Meta:
        ordering = ['book__title', '-due_back']

        def __str__(self):
            return f'{self.id} ({self.book.title})'

    def get_absolute_url(self):
        return reverse('bookinstance-detail', args=[str(self.id)])



