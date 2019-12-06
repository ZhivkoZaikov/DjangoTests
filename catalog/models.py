from django.db import models
from django.urls import reverse

from . import validators

class Genre(models.Model):
    name = models.CharField(max_length=200, help_text='Enter a book genre (e.g. Science Fiction)', unique=True)
    image = models.ImageField(upload_to='images/genres', null=True, blank=True)
    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('genre-list', args=[str(self.id)])

class Language(models.Model):
    name = models.CharField(max_length=50,
                            help_text='Enter the book language(e.g. Spanish, English, Chinese, etc)', unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Language'

class Author(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    date_of_birth = models.DateField(null=True, blank=True, validators=[validators.validate_date_not_in_future, ])
    # set 'Died' as a verbose name
    date_of_death = models.DateField('Died', null=True, blank=True, validators=[validators.validate_date_not_in_future, ])
    image = models.ImageField(upload_to='images/authors/', null=True, blank=True)
    about_the_author = models.TextField(max_length=1000, null=True, blank=True)
    class Meta:
        ordering = ['last_name', 'first_name']

    def get_absolute_url(self):
        return reverse('author-detail', args=[str(self.id)])

    def __str__(self):
        return f'{self.first_name}, {self.last_name}'

    def get_name(self):
        return f'{self.last_name}, {self.first_name} '

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
