from datetime import datetime
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SelectMultipleField, DateTimeField, BooleanField
from wtforms.validators import DataRequired, URL, Regexp, Optional
from enum import Enum

class GenreEnum(Enum):
    Alternative = 'Alternative',
    Blues = 'Blues',
    Classical = 'Classical',
    Country = 'Country',
    Electronic = 'Electronic',
    Folk = 'Folk',
    Funk = 'Funk',
    HipHop = 'Hip-Hop',
    HeavyMetal = 'Heavy Metal',
    Instrumental = 'Instrumental',
    Jazz = 'Jazz',
    MusicalTheatre = 'Musical Theatre',
    Pop = 'Pop',
    Punk = 'Punk',
    RAndB = 'R&B',
    Reggae = 'Reggae',
    RocknRoll = 'Rock n Roll',
    Soul = 'Soul',
    Other = 'Other',

class StateEnum(Enum):
    AL = 'AL',
    AK = 'AK',
    AZ = 'AZ',
    AR = 'AR',
    CA = 'CA',
    CO = 'CO',
    CT = 'CT',
    DE = 'DE',
    DC = 'DC',
    FL = 'FL',
    GA = 'GA',
    HI = 'HI',
    ID = 'ID',
    IL = 'IL',
    IN = 'IN',
    IA = 'IA',
    KS = 'KS',
    KY = 'KY',
    LA = 'LA',
    ME = 'ME',
    MT = 'MT',
    NE = 'NE',
    NV = 'NV',
    NH = 'NH',
    NJ = 'NJ',
    NM = 'NM',
    NY = 'NY',
    NC = 'NC',
    ND = 'ND',
    OH = 'OH',
    OK = 'OK',
    OR = 'OR',
    MD = 'MD',
    MA = 'MA',
    MI = 'MI',
    MN = 'MN',
    MS = 'MS',
    MO = 'MO',
    PA = 'PA',
    RI = 'RI',
    SC = 'SC',
    SD = 'SD',
    TN = 'TN',
    TX = 'TX',
    UT = 'UT',
    VT = 'VT',
    VA = 'VA',
    WA = 'WA',
    WV = 'WV',
    WI = 'WI',
    WY = 'WY',

class ShowForm(FlaskForm):
    artist_id = StringField(
        'Artist ID'
    )
    venue_id = StringField(
        'Venue ID'
    )
    start_time = DateTimeField(
        'Start Time',
        validators=[DataRequired()],
        default= datetime.today()
    )

class VenueForm(FlaskForm):
    name = StringField(
        'Name', validators=[DataRequired()]
    )
    city = StringField(
        'City', validators=[DataRequired()]
    )
    state = SelectField(
        'State', validators=[DataRequired()],
        choices=[(e.value[0], e.value[0]) for e in StateEnum]
    )
    address = StringField(
        'Address', validators=[DataRequired()]
    )
    phone = StringField(
        'Phone', validators=[DataRequired(),
                             Regexp('^\d{3}-\d{3}-\d{4}$',
                                    message='Invalid phone number'),]
    )
    image_link = StringField(
        'Image Link', validators=[Optional(), URL()]
    )
    genres = SelectMultipleField(
        'Genres', validators=[DataRequired()],
        choices=[(e.value[0], e.value[0]) for e in GenreEnum]
    )
    facebook_link = StringField(
        'Facebook Link', validators=[Optional(), URL()]
    )
    website_link = StringField(
        'Website Link', validators=[Optional(), URL()]
    )

    seeking_talent = BooleanField('Seeking Talent')

    seeking_description = StringField(
        'Seeking Description'
    )

class ArtistForm(FlaskForm):
    name = StringField(
        'Name', validators=[DataRequired()]
    )
    city = StringField(
        'City', validators=[DataRequired()]
    )
    state = SelectField(
        'State', validators=[DataRequired()],
        choices=[(e.value[0], e.value[0]) for e in StateEnum]
    )
    phone = StringField(
        'Phone', validators=[DataRequired(),
                             Regexp('^\d{3}-\d{3}-\d{4}$',
                                    message='Invalid phone number'),]
    )
    image_link = StringField(
        'Image Link', validators=[Optional(), URL()]
    )
    genres = SelectMultipleField(
        'Genres', validators=[DataRequired()],
        choices=[(e.value[0], e.value[0]) for e in GenreEnum]
     )
    facebook_link = StringField(
        'Facebook Link', validators=[Optional(), URL()]
     )

    website_link = StringField(
        'Website Link', validators=[Optional(), URL()]
     )

    seeking_venue = BooleanField('Seeking Venue')

    seeking_description = StringField(
        'Seeking Description'
     )
