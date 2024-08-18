#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from collections import deque
from flask import Flask, jsonify, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from sqlalchemy.sql import case
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
import config
from flask_migrate import Migrate
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

# in-memory recent queries
recent_queries = deque(maxlen=10)

app = Flask(__name__)
moment = Moment(app)
app.config.from_object(config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Show(db.Model):
  __tablename__ = 'Show'
  venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), primary_key=True, nullable=False)
  artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'), primary_key=True, nullable=False)
  start_time = db.Column(db.DateTime, primary_key=True)

class Venue(db.Model):
  __tablename__ = 'Venue'
  id = db.Column(db.Integer, primary_key=True, nullable=False)
  name = db.Column(db.String)
  city = db.Column(db.String(120))
  state = db.Column(db.String(120))
  address = db.Column(db.String(120))
  phone = db.Column(db.String(120))
  genres = db.Column(db.String)
  image_link = db.Column(db.String(500))
  facebook_link = db.Column(db.String(120))
  website = db.Column(db.String(120))
  seeking_talent = db.Column(db.Boolean())
  seeking_description = db.Column(db.String)

  def __repr__(self):
    return (f'<Venue id={self.id} name={self.name} city={self.city} state={self.state} '
            f'address={self.address} phone={self.phone} genres={self.genres} '
            f'image_link={self.image_link} facebook_link={self.facebook_link} '
            f'website={self.website} seeking_talent={self.seeking_talent} '
            f'seeking_description={self.seeking_description}>')
       
class Artist(db.Model):
  __tablename__ = 'Artist'
  id = db.Column(db.Integer, primary_key=True, nullable=False)
  name = db.Column(db.String)
  city = db.Column(db.String(120))
  state = db.Column(db.String(120))
  phone = db.Column(db.String(120))
  genres = db.Column(db.String)
  image_link = db.Column(db.String(500))
  facebook_link = db.Column(db.String(120))
  website = db.Column(db.String(120))
  seeking_venue = db.Column(db.Boolean())
  seeking_description = db.Column(db.String)
  availability = db.Column(db.String)

  def __repr__(self):
    return (
        f"<Artist id={self.id}, name={self.name}, city={self.city}, state={self.state}, "
        f"phone={self.phone}, genres={self.genres}, image_link={self.image_link}, "
        f"facebook_link={self.facebook_link}, website={self.website}, "
        f"seeking_venue={self.seeking_venue}, seeking_description={self.seeking_description}, "
        f"availability={self.availability}>"
    )

def get_availability_list(availability_artist) -> list[dict]:
  """
  Parse availability string to a list of dict
  """
  try:
    if availability_artist is not None:
      availability_list = list()
      for a in availability_artist.split(','):
        if a:
          times = a.split(';')
          availability_list.append({'start_time': times[0], 'end_time': times[1]})
      return availability_list
    else:
      return list()
  except Exception as e:
    print(e)
    flash(f'Invalid availability: {availability_artist}')
    return list()
  
#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  if isinstance(value, str):
    value = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(value, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

with app.app_context():
   db.create_all()

@app.route('/')
def index():
  return render_template('pages/home.html', recent=recent_queries)


#  Venues
#  ----------------------------------------------------------------
@app.route('/venues')
def venues():
  now_time = datetime.now()
  data = list()
  cities_and_states = db.session.query(Venue.city, Venue.state).distinct().all()
  for city, state in cities_and_states:
    city_entry = dict()
    city_entry['city'] = city
    city_entry['state'] = state
    venues = Venue.query.filter(Venue.city == city, Venue.state == state).all()
    venues_data = list()
    for venue in venues:
      num_upcoming_shows = Show.query.filter(Show.venue_id == venue.id, Show.start_time >= now_time).count()
      venues_data.append({
         'id': venue.id,
         'name': venue.name,
         'num_upcoming_shows': num_upcoming_shows
      })
    city_entry['venues'] = venues_data
    data.append(city_entry)
  return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  now_time = datetime.now()
  search_term = request.form.get('search_term', '')
  search_res = db.session.query(Venue.id, Venue.name).filter(Venue.name.ilike(f'%{search_term}%'))
  data = list()
  for venue in search_res.all():
    data.append({
      'id': venue.id,
      'name': venue.name,
      'num_upcoming_shows': Show.query.filter(Show.venue_id==venue.id, Show.start_time >= now_time).count()
    })
  res = {'count': search_res.count(), 'data': data}
  return render_template('pages/search_venues.html', results=res, search_term=search_term)

@app.route('/artists_and_venues/search', methods=['POST'])
def search_by_city_and_state():
  # Searching by "San Francisco, CA" should return all artists or venues in San Francisco, CA"

  # get city and state
  search_term = request.form.get('search_term', '')
  splitted = search_term.split(',')

  data = list()
  if len(splitted) == 2:
    city, state = splitted[0].strip(), splitted[1].strip()

    # search venues
    venues = db.session.query(Venue.id, Venue.name).filter(Venue.city.ilike(f'{city}'), Venue.state.ilike(f'{state}'))
    for venue in venues.all():
      data.append({
        'venue_id': venue.id,
        'venue_name': venue.name,
      })
    
    # search artists
    artists = db.session.query(Artist.id, Artist.name).filter(Artist.city.ilike(f'{city}'), Artist.state.ilike(f'{state}'))
    for artist in artists.all():
      data.append({
        'artist_id': artist.id,
        'artist_name': artist.name,
      })
  res = {'count': len(data), 'data': data}
  return render_template('pages/search_by_city_and_state.html', results=res, search_term=search_term)

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  venue = Venue.query.get(venue_id)
  upcoming_shows = db.session.query(Show.artist_id, Artist.name.label('artist_name'), Artist.image_link.label('artist_image_link'), Show.start_time) \
    .join(Artist) \
    .filter(Show.venue_id==venue_id, Show.start_time >= datetime.now())
  past_shows = db.session.query(Show.artist_id, Artist.name.label('artist_name'), Artist.image_link.label('artist_image_link'), Show.start_time) \
    .join(Artist) \
    .filter(Show.venue_id==venue_id, Show.start_time < datetime.now())
  genres = list()
  if venue.genres is not None:
     genres = venue.genres.split(',')
  venue_data = {
    "id": venue.id,
    "name": venue.name,
    "genres": genres,
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website": venue.website,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": past_shows.count(),
    "upcoming_shows_count": upcoming_shows.count(),
  }

  # add to recent queries
  rec = {'venue_id': venue_id, 'venue_name': venue.name}
  if rec not in recent_queries:
    recent_queries.append(rec)

  return render_template('pages/show_venue.html', venue=venue_data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  form = VenueForm(request.form)
  try:
    venue = Venue()
    form.populate_obj(venue)
    venue.genres = ','.join(form.genres.data)
    db.session.add(venue)
    db.session.commit()
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  except Exception as e:
     print(e)
     flash('An error occurred. Venue could not be created.')
     db.session.rollback()
  finally:
     db.session.close()
  return render_template('pages/home.html', recent=recent_queries)

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  try:
    venue = Venue.query.get(venue_id)
    db.session.delete(venue)
    db.session.commit()
  except Exception as e:
    print(e)
    flash('An error occurred.')
    db.session.rollback()
  finally:
    db.session.close()
  return jsonify({'success': True})

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  return render_template('pages/artists.html', artists=Artist.query.order_by('name').all())

@app.route('/artists/search', methods=['POST'])
def search_artists():
  now_time = datetime.now()
  search_term = request.form.get('search_term', '')
  search_res = db.session.query(Artist.id, Artist.name).filter(Artist.name.ilike(f'%{search_term}%'))
  data = list()
  for artist in search_res.all():
    data.append({
      'id': artist.id,
      'name': artist.name,
      'num_upcoming_shows': Show.query.filter(Show.artist_id==artist.id, Show.start_time >= now_time).count()
    })
  res = {'count': search_res.count(), 'data': data}

  return render_template('pages/search_artists.html', results=res, search_term=search_term)

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  now_time = datetime.now()
  artist = Artist.query.get(artist_id)
  if artist is None:
    flash(f'Artist ID {artist_id} does not exist')
    return render_template('pages/home.html', recent=recent_queries)
  
  upcoming_shows = db.session.query(Venue.id.label('venue_id'), Venue.name.label('venue_name'), Venue.image_link.label('venue_image_link'), Show.start_time) \
    .join(Show) \
    .filter(Show.artist_id==artist_id, Show.start_time >= now_time)
  past_shows = db.session.query(Venue.id.label('venue_id'), Venue.name.label('venue_name'), Venue.image_link.label('venue_image_link'), Show.start_time) \
    .join(Show) \
    .filter(Show.artist_id==artist_id, Show.start_time < now_time)
  
  # populate genres
  genres = list()
  if artist.genres is not None:
     genres = artist.genres.split(',')
  
  # populate availability list
  availability_list = get_availability_list(artist.availability)

  artist_data = {
    "id": artist.id,
    "name": artist.name,
    "genres": genres,
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description,
    "image_link": artist.image_link,
    "upcoming_shows": upcoming_shows,
    "upcoming_shows_count": upcoming_shows.count(),
    "past_shows": past_shows,
    "past_shows_count": past_shows.count(),
    "availability": availability_list
  }

  # add to recent queries
  rec = {'artist_id': artist_id, 'artist_name': artist.name}
  if rec not in recent_queries:
    recent_queries.append(rec)

  return render_template('pages/show_artist.html', artist=artist_data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  try:
    artist=Artist.query.get(artist_id)
    form = ArtistForm(obj=artist)
    availability_list = get_availability_list(artist.availability)
    print(availability_list)

    if artist.genres is not None:
      form.genres.data = artist.genres.split(',')

    return render_template('forms/edit_artist.html', form=form, artist=artist, availability_list=availability_list)
  
  except Exception as e:
    print(e)
    flash('An error occurred.')
    return render_template('pages/home.html', recent=recent_queries)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # artist record with ID <artist_id> using the new attributes
  try:
    form = ArtistForm(request.form)
    artist = Artist.query.get(artist_id)
    form.populate_obj(artist)
    artist.genres = ','.join(form.genres.data)

    # serialize availability list
    start_times = request.form.getlist('availabilities[][start_time]')
    end_times = request.form.getlist('availabilities[][end_time]')
    artist.availability = ','.join([f'{start_time};{end_time}' for start_time, end_time in zip(start_times, end_times)])
    print(artist.availability)

    db.session.commit()
    flash(f'Artist {artist.name} was successfully updated!')
  except Exception as e:
    print(e)
    flash('An error occurred. Artist could not be updated.')
    db.session.rollback()
  finally:
    db.session.close()  

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  try:
    venue = Venue.query.get(venue_id)
    form = VenueForm(obj=venue)
    if venue.genres is not None:
      form.genres.data = venue.genres.split(',')
  except Exception as e:
     print(e)
     flash('An error occurred.')

  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  try:
    form = VenueForm(request.form)
    venue = Venue.query.get(venue_id)
    form.populate_obj(venue)
    venue.genres = ','.join(form.genres.data)
    db.session.commit()
    flash('Venue ' + request.form['name'] + ' was successfully updated!')
  except Exception as e:
    print(e)
    flash('An error occurred. Venue could not be updated.')
    db.session.rollback()
  finally:
    db.session.close()

  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  form = ArtistForm(request.form)
  try:
    artist = Artist()
    form.populate_obj(artist)
    artist.genres = ','.join(form.genres.data)
    db.session.add(artist)
    db.session.commit()
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  except Exception as e:
     print(e)
     flash('An error occurred. Artist could not be listed.')
     db.session.rollback()
  finally:
     db.session.close()

  return render_template('pages/home.html', recent=recent_queries)

#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  shows = db.session.query(Show.venue_id, 
                           Venue.name.label('venue_name'), 
                           Show.artist_id, 
                           Artist.name.label('artist_name'),
                           Artist.image_link.label('artist_image_link'),
                           Show.start_time).join(Venue).join(Artist).all()
  
  return render_template('pages/shows.html', shows=shows)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  form = ShowForm(request.form)
  try:
    show = Show()
    form.populate_obj(show)

    # check artist
    artist = Artist.query.get(show.artist_id)
    if artist is None:
      flash(f'Artist ID {show.artist_id} does not exist')
      return render_template('forms/new_show.html', form=form)
    
    # check artist availability
    availability_list = get_availability_list(artist.availability)
    available = False
    for a in availability_list:
      if datetime.fromisoformat(a['start_time']) <= show.start_time <= datetime.fromisoformat(a['end_time']):
        available = True
        break
    
    if not available:
      flash('The artist is not available at this time!')
      return render_template('forms/new_show.html', form=form)

    db.session.add(show)
    db.session.commit()
    flash('Show was successfully listed!')
  except Exception as e:
     print(e)
     flash(f'An error occurred: {e}')
     db.session.rollback()
  finally:
     db.session.close()

  return render_template('pages/home.html', recent=recent_queries)

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()
