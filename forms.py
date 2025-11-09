from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, IntegerField, TextAreaField, BooleanField, DateField, SubmitField, PasswordField
from wtforms.validators import DataRequired, Optional, NumberRange, ValidationError
from datetime import datetime

# Define valid genres for each media type
VALID_GENRES = {
    "Movie": ["Action/Thriller", "Animated", "Comedy", "Documentary", "Drama", "Historical", "Horror", "Indie", "Psychological", "Romance", "Scifi"],
    "Book": ["Comic", "Crime", "Fantasy", "Historical Fiction", "Horror", "Literary", "Mystery", "Nonfiction", "Scifi", "Thriller"],
    "TV": ["Animated", "Comedy", "Documentary", "Drama", "Dramedy"],
    "Music": ["Classic Rock", "Country", "Electronic", "Folk", "Indie", "Jazz", "Pop", "Postrock", "Rap", "Rock"],
    "Sports": ["Auto Racing", "Baseball", "Basketball", "Football", "Olympics", "Other", "Soccer"],
    "Podcast": ["Commentary", "Entertainment", "News"],
    "Museum": ["Art", "History", "Other", "Science"]
}

class LoginForm(FlaskForm):
    # this field can accept either username or email
    identifier = StringField('Username or Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')

class EntryForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    
    media_type = SelectField('Media Type', choices=sorted([
        ('Book', 'Book'),
        ('Movie', 'Movie'),
        ('Museum', 'Museum'),
        ('Music', 'Music'),
        ('Podcast', 'Podcast'),
        ('Sports', 'Sports'),
        ('TV', 'TV')
    ], key=lambda x: x[1]), validators=[DataRequired()])
    
    genre = SelectField('Genre', choices=[], validators=[DataRequired()])

    def validate_genre(self, field):
        if self.media_type.data and field.data:
            valid_genres = VALID_GENRES.get(self.media_type.data, [])
            # Convert both the input and valid genres to lowercase for comparison
            if field.data.strip() not in [g.strip() for g in valid_genres]:
                # Add debug information to the error message
                raise ValidationError(
                    f'Invalid genre "{field.data}" for {self.media_type.data}. '
                    f'Must be one of: {", ".join(valid_genres)}. '
                    f'Received genre length: {len(field.data)}, '
                    f'First char code: {ord(field.data[0]) if field.data else "N/A"}'
                )

    def set_genre_choices(self, media_type):
        self.genre.choices = [(g, g) for g in VALID_GENRES.get(media_type, [])]

    source = SelectField('Source', choices=sorted([
        ('Amazon', 'Amazon'),
        ('Apple', 'Apple'),
        ('HBO Max', 'HBO Max'),
        ('Hulu', 'Hulu'),
        ('Netflix', 'Netflix'),
        ('Other', 'Other'),
        ('Paramount', 'Paramount'),
        ('Spotify', 'Spotify'),
        ('Theater', 'Theater'),
        ('TV Network/Uverse', 'TV Network/Uverse'),
        ('Tubi', 'Tubi'),
        ('You Tube', 'You Tube')
    ], key=lambda x: x[0]), validators=[Optional()])

    year_released = IntegerField('Year Released', validators=[DataRequired(), NumberRange(min=1800, max=datetime.now().year)])
    date = DateField('Date', validators=[Optional()])
    notes = TextAreaField('Notes', validators=[Optional()])
    rating = SelectField('Rating', 
                      choices=[('5', '5'), ('4', '4'), ('3', '3'), ('2', '2'), ('1', '1')],
                      validators=[Optional()],
                      coerce=int)
    dnf = BooleanField('DNF')
    recommended = BooleanField('Recommended')
    foreign = BooleanField('Foreign')
    country = StringField('Country', validators=[Optional()])

    submit = SubmitField('Submit')