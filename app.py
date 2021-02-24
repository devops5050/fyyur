#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import sys
import json
import dateutil.parser
import babel
from sqlalchemy import func
from flask import Flask, render_template, request, Response, flash, redirect, url_for, abort
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    genres = db.Column(db.ARRAY(db.String()))
    address = db.Column(db.String(120))
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean)
    seeking_description = db.Column(db.String(500))
    shows = db.relationship('Show', backref="venue", lazy=True)

    def __repr__(self):
        return '<Venue {}>'.format(self.name)


class Artist(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    genres = db.Column(db.ARRAY(db.String))
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    website = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean)
    seeking_description = db.Column(db.String(500))
    shows = db.relationship('Show', backref="artist", lazy=True)

    def __repr__(self):
        return '<Artist {}>'.format(self.name)


class Show(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey(
        'artist.id'), nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey('venue.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return '<Show {}{}>'.format(self.artist_id, self.venue_id)

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():

  venues_list = Venue.query.with_entities(Venue.city, Venue.state).distinct().all()

  data = []
  print('venue list')
  print(venues_list)
  for venue_item in venues_list:
    venueslist = Venue.query.filter_by(state=venue_item.state).filter_by(city=venue_item.city).all()

    venuedata = []

    for venue in venueslist:
      venuedata.append({
        "id": venue.id,
        "name": venue.name
      })

    data.append({
      "city": venue_item.city,
      "state": venue_item.state,
      "venues": venuedata
    })

  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():

  search_term = request.form.get('search_term', '')
  print("Search term is " + search_term)
  search_results = Venue.query.filter(Venue.name.ilike(f'%{search_term}%')).all()
  data = []
  response = {}
  
  if search_results:
    for result in search_results:
      data.append({
        "id": result.id,
        "name": result.name,
      })
      response = {
        "count": len(search_results),
        "data": data
      }
  else:
    response = {
        "count": 0,
        "data": data
      }

  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):

  venue_item = Venue.query.get(venue_id)

  futureshows = Show.query.join(Artist).filter(Show.venue_id==venue_id).filter(Show.start_time>datetime.now()).all()
  futureshows_data = []
  # print('future shows')
  # print(len(futureshows))

  pastshows = Show.query.join(Artist).filter(Show.venue_id==venue_id).filter(Show.start_time<datetime.now()).all()
  pastshows_data = []
  # print('past shows')
  # print(len(pastshows))

  # Ref: https://knowledge.udacity.com/questions/386723
  for show_item in pastshows:
    pastshows_data.append({
      "artist_id": show_item.artist_id,
      "artist_name": show_item.artist.name,
      "artist_image_link": show_item.artist.image_link,
      "start_time": show_item.start_time.strftime("%m/%d/%Y, %H:%M")
    })

  for show_item in futureshows:
    futureshows_data.append({
      "artist_id": show_item.artist_id,
      "artist_name": show_item.artist.name,
      "artist_image_link": show_item.artist.image_link,
      "start_time": show_item.start_time.strftime("%m/%d/%Y, %H:%M")    
    })

  data = {
    "id": venue_item.id,
    "name": venue_item.name,
    "genres": venue_item.genres,
    "address": venue_item.address,
    "city": venue_item.city,
    "state": venue_item.state,
    "phone": venue_item.phone,
    "website": venue_item.website,
    "facebook_link": venue_item.facebook_link,
    "seeking_talent": venue_item.seeking_talent,
    "seeking_description": venue_item.seeking_description,
    "image_link": venue_item.image_link,
    "upcoming_shows": futureshows_data,
    "upcoming_shows_count": len(futureshows_data),
    "past_shows": pastshows_data,
    "past_shows_count": len(pastshows_data),
  }

  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():

  error = False

  try:
    name = request.form['name']
    city = request.form['city']
    state = request.form['state']
    address = request.form['address']
    phone = request.form['phone']
    genres = request.form.getlist('genres')
    facebook_link = request.form['facebook_link']
    image_link = request.form['image_link']

    venue = Venue(name=name, city=city, state=state, address=address, phone=phone, genres=genres, facebook_link=facebook_link, image_link=image_link)
    db.session.add(venue)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  if error:
    flash('An error occurred. Venue ' + request.form['name']+ ' could not be listed.')
  if not error:
    flash('Venue ' + request.form['name'] + ' was successfully listed!')

  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  try: 
    Venue.query.filter(Venue.id == venue_id).delete()
    db.session.commit()
  except:
    db.session.rollback()
  finally:
    db.session.close()

  return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  data = Artist.query.all()
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():

  search_term = request.form.get('search_term', '')
  print("Search term is " + search_term)
  search_results = Artist.query.filter(Artist.name.ilike(f'%{search_term}%')).all()
  data = []
  response = {}
  
  if search_results:
    for result in search_results:
      data.append({
        "id": result.id,
        "name": result.name,
      })
      response = {
        "count": len(search_results),
        "data": data
      }
  else:
    response = {
        "count": 0,
        "data": data
      }

  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  artist_detail = Artist.query.get(artist_id)
  # print('artist_detail')
  # print(artist_detail)

  data={
    "id": artist_detail.id,
    "name": artist_detail.name,
    "genres": artist_detail.genres,
    "city": artist_detail.city,
    "state": artist_detail.state,
    "phone": artist_detail.phone,
    "website": artist_detail.website,
    "facebook_link": artist_detail.facebook_link,
    "seeking_venue": artist_detail.seeking_venue,
    "seeking_description": artist_detail.seeking_description,
    "image_link": artist_detail.image_link,
  }

  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):

  artist = Artist.query.filter(Artist.id == artist_id).first()
  form = ArtistForm(obj=artist)

  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  error = False

  artist = Artist.query.get(artist_id)

  try:
    name = request.form.get('name')
    city = request.form.get('city')
    state = request.form.get('state')
    phone = request.form.get('phone')
    genres = request.form.getlist('genres')
    facebook_link = request.form.get('facebook_link')

    artist.name = name
    artist.city = city
    artist.state = state
    artist.phone = phone
    artist.genres = genres
    artist.facebook_link = facebook_link

    db.session.add(artist)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  if error:
    flash('An error occurred. artist ' + request.form['name']+ ' could not be updated.')
  if not error:
    flash('Artist ' + request.form.get('name') + ' was successfully updated!')

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):

  venue = Venue.query.filter(Venue.id == venue_id).first()
  form = VenueForm(obj=venue)

  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):

  error = False

  venue = Venue.query.get(venue_id)

  try:
    name = request.form.get('name')
    city = request.form.get('city')
    state = request.form.get('state')
    address = request.form.get('address')
    phone = request.form.get('phone')
    genres = request.form.getlist('genres')
    facebook_link = request.form.get('facebook_link')
    image_link = request.form.get('image_link')

    venue.name = name
    venue.city = city
    venue.state = state
    venue.address = address
    venue.phone = phone
    venue.genres = genres
    venue.facebook_link = facebook_link
    venue.image_link = image_link

    db.session.add(venue)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  if error:
    flash('An error occurred. Venue ' + request.form['name']+ ' could not be updated.')
  if not error:
    flash('Venue ' + request.form['name'] + ' was successfully updated!')

  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  error = False
  
  try: 
    name = request.form['name']
    city = request.form['city']
    state = request.form['state']
    phone = request.form['phone']
    genres = request.form.getlist('genres')
    facebook_link = request.form['facebook_link']
    image_link = request.form['image_link']

    artist = Artist(name=name, city=city, state=state, phone=phone, genres=genres, facebook_link=facebook_link, image_link=image_link)
    db.session.add(artist)
    db.session.commit()
  except: 
    error = True
    db.session.rollback()
    logging.exception("message")
    print(sys.exc_info())
  finally: 
    db.session.close()
  if error: 
    flash('An error occurred. Venue ' + request.form['name']+ ' could not be listed.')
  if not error: 
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  return render_template('pages/home.html')

#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():

  data = []
  # Get Artist data which has reference to show table
  artistslist = Artist.query.all()

  for artist in artistslist:
    # print('Artist Name: ' + artist.name + ', Artist ID: '+ str(artist.id))
    # print(artist.shows)
    # Get all shows against an artist
    for venval in artist.shows:
      venueslist = Venue.query.filter_by(id=venval.venue_id).all()
      # print('Venue Name: ' + venueslist[0].name + ', Venue ID: ' + str(venueslist[0].id))
      data.append({
        "artist_name": artist.name,
        "artist_id": artist.id,
        "venue_name": venueslist[0].name,
        "venue_id": venueslist[0].id,
        "start_time": str(venval.start_time),
        "artist_image_link": artist.image_link
      })

  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  error = False
  
  try: 
    artist_id = request.form['artist_id']
    venue_id = request.form['venue_id']
    start_time = request.form['start_time']

    print('Artist: ' + str(artist_id) + ', Venue: ' + str(venue_id) + ', Start Time: ' + str(start_time))

    show = Show(artist_id=artist_id, venue_id=venue_id, start_time=start_time)
    db.session.add(show)
    db.session.commit()
  except: 
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally: 
    print(sys.exc_info())
    db.session.close()
  if error: 
    flash('An error occurred. ')
  if not error: 
    flash('Show was successfully listed!')
  return render_template('pages/home.html')

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

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
