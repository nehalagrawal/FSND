#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from extension import csrf
import sys
from datetime import datetime
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)
csrf.init_app(app)
# TODO: connect to a local postgresql database

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Show(db.Model):
  __tablename__ = 'Show'

  id = db.Column(db.Integer, primary_key=True)
  venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), nullable=False)
  artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'), nullable=False)
  start_time = db.Column(db.DateTime(), nullable=False)

  def __repr__(self):
    return f'<Show {self.id}>'

class Venue(db.Model):
  __tablename__ = 'Venue'

  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String, nullable=False)
  city = db.Column(db.String(120), nullable=False)
  state = db.Column(db.String(120), nullable=False)
  address = db.Column(db.String(120), nullable=False)
  phone = db.Column(db.String(120), nullable=False)
  genres = db.Column(db.String(120), nullable=False)
  facebook_link = db.Column(db.String(120), nullable=False)
  image_link = db.Column(db.String(500))
  website = db.Column(db.String(120))
  seeking_talent = db.Column(db.Boolean)
  seeking_description = db.Column(db.String)
  shows = db.relationship('Show', backref='venue', lazy=True)

  def __repr__(self):
    return f'<Venue {self.id} {self.name}>'

    # TODO: implement any missing fields, as a database migration using Flask-Migrate

class Artist(db.Model):
  __tablename__ = 'Artist'

  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String, nullable=False)
  city = db.Column(db.String(120), nullable=False)
  state = db.Column(db.String(120), nullable=False)
  phone = db.Column(db.String(120), nullable=False)
  genres = db.Column(db.String(120), nullable=False)
  facebook_link = db.Column(db.String(120), nullable=False)
  image_link = db.Column(db.String(500))
  website = db.Column(db.String(120))
  seeking_venue = db.Column(db.Boolean)
  seeking_description = db.Column(db.String)
  shows = db.relationship('Show', backref='artist', lazy=True)

  def __repr__(self):
    return f'<Artist {self.id} {self.name}>'

    # TODO: implement any missing fields, as a database migration using Flask-Migrate

# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.

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

@csrf.exempt
@app.route('/venues')
def venues():
  city_state = db.session.query(Venue.city, Venue.state).distinct(Venue.city, Venue.state).all()
  data = []
  for pair in city_state:
    venues = db.session.query(Venue).filter_by(city=pair.city, state=pair.state).all()
    venue_dict_list = []
    for venue in venues:
      up_coming_shows = db.session.query(Show).filter_by(venue_id=venue.id).filter(Show.start_time > datetime.now()).all()
      venue_dict = {
        "id": venue.id,
        "name": venue.name,
        "num_upcoming_shows": len(up_coming_shows)
      }
      venue_dict_list.append(venue_dict)
    data_dict = {
      "city": pair.city,
      "state": pair.state,
      "venues": venue_dict_list
    }
    data.append(data_dict)
  return render_template('pages/venues.html', areas=data);

@csrf.exempt
@app.route('/venues/search', methods=['POST'])
def search_venues():
  search_str=request.form.get('search_term')
  search_results = db.session.query(Venue).filter(Venue.name.ilike('%{}%'.format(search_str))).all()
  data = []
  for result in search_results:
    num_upcoming_shows = db.session.query(Show).filter_by(venue_id=result.id).filter(Show.start_time > datetime.now()).all()
    data_dict = {
      "id": result.id,
      "name": result.name,
      "num_upcoming_shows": len(num_upcoming_shows)
    }
    data.append(data_dict)

  response={
    "count": len(search_results),
    "data": data
  }

  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@csrf.exempt
@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  
  venue = db.session.query(Venue).filter_by(id=venue_id).all()[0]
  past_shows = db.session.query(Show).filter_by(venue_id=venue_id).filter(Show.start_time <= datetime.now()).all()
  upcoming_shows = db.session.query(Show).filter_by(venue_id=venue_id).filter(Show.start_time > datetime.now()).all()
  past_shows_list = []
  upcoming_shows_list = []
  for show in past_shows:
    show_dict = {
      "artist_id": show.artist_id,
      "artist_name": db.session.query(Artist.name).filter_by(id=show.artist_id).all()[0][0],
      "artist_image_link": db.session.query(Artist.image_link).filter_by(id=show.artist_id).all()[0][0],
      "start_time": show.start_time.strftime("%m/%d/%Y, %H:%M:%S")
    }
    past_shows_list.append(show_dict)

  for show in upcoming_shows:
    show_dict = {
      "artist_id": show.artist_id,
      "artist_name": db.session.query(Artist.name).filter_by(id=show.artist_id).all()[0][0],
      "artist_image_link": db.session.query(Artist.image_link).filter_by(id=show.artist_id).all()[0][0],
      "start_time": show.start_time.strftime("%m/%d/%Y, %H:%M:%S")
    }
    upcoming_shows_list.append(show_dict)

  data = {
    "id": venue_id,
    "name": venue.name,
    "genres": venue.genres[1:-1].split(","),
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website": venue.website,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "image_link": venue.image_link,
    "past_shows": past_shows_list,
    "upcoming_shows": upcoming_shows_list,
    "past_shows_count": len(past_shows_list),
    "upcoming_shows_count": len(upcoming_shows_list),
  }
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------
@csrf.exempt
@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@csrf.exempt
@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  form = VenueForm(request.form)
  if form.validate_on_submit():
    try:
      name = form.name.data
      city = form.city.data
      state = form.state.data
      address = form.address.data
      phone = form.phone.data
      genres = form.genres.data
      facebook_link = form.facebook_link.data
      website = form.website.data
      image_link = form.image_link.data

      venue = Venue(name=name, city=city, state=state, address=address, phone=phone, genres=genres, facebook_link=facebook_link, website=website, image_link=image_link)

      db.session.add(venue)
      db.session.commit()

      flash('Venue ' + name + ' was successfully listed!')

    except:
      db.session.rollback()
      print(sys.exc_info())
      flash('An error occurred. Venue ' + form.name.data + ' could not be listed.')

    finally:
      db.session.close()
  else:
    print(form.errors)
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return None

#  Artists
#  ----------------------------------------------------------------
@csrf.exempt
@app.route('/artists')
def artists():
  data = []
  artists = db.session.query(Artist).all()
  for artist in artists:
    artist_dict = {
      "id": artist.id,
      "name": artist.name
    }
    data.append(artist_dict)
  return render_template('pages/artists.html', artists=data)

@csrf.exempt
@app.route('/artists/search', methods=['POST'])
def search_artists():
  
  search_str = request.form.get('search_term')
  search_results = db.session.query(Artist).filter(Artist.name.ilike('%{}%'.format(search_str))).all()
  data = []
  for result in search_results:
    num_upcoming_shows = db.session.query(Show).filter_by(artist_id=result.id).filter(Show.start_time > datetime.now()).all()
    data_dict = {
      "id": result.id,
      "name": result.name,
      "num_upcoming_shows": len(num_upcoming_shows)
    }
    data.append(data_dict)

  response = {
    "count": len(search_results),
    "data": data
  }

  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@csrf.exempt
@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  
  artist = db.session.query(Artist).filter_by(id=artist_id).all()[0]
  past_shows = db.session.query(Show).filter_by(artist_id=artist_id).filter(Show.start_time <= datetime.now()).all()
  up_coming_shows = db.session.query(Show).filter_by(artist_id=artist_id).filter(Show.start_time > datetime.now()).all()
  past_shows_list = []
  up_coming_shows_list = []
  for show in past_shows:
    show_dict = {
      "venue_id": show.venue_id,
      "venue_name": db.session.query(Venue.name).filter_by(id=show.venue_id).all()[0][0],
      "venue_image_link": db.session.query(Venue.image_link).filter_by(id=show.venue_id).all()[0][0],
      "start_time": show.start_time.strftime("%m/%d/%Y, %H:%M:%S")
    }
    past_shows_list.append(show_dict)

  for show in up_coming_shows:
    show_dict = {
      "venue_id": show.venue_id,
      "venue_name": db.session.query(Venue.name).filter_by(id=show.venue_id).all()[0][0],
      "venue_image_link": db.session.query(Venue.image_link).filter_by(id=show.venue_id).all()[0][0],
      "start_time": show.start_time.strftime("%m/%d/%Y, %H:%M:%S")
    }
    up_coming_shows_list.append(show_dict)

  data = {
    "id": artist_id,
    "name": artist.name,
    "genres": artist.genres[1:-1].split(","),
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "website": artist.website,
    "facebook_link": artist.facebook_link,
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description,
    "image_link": artist.image_link,
    "past_shows": past_shows_list,
    "upcoming_shows": up_coming_shows_list,
    "past_shows_count": len(past_shows_list),
    "upcoming_shows_count": len(up_coming_shows_list),
  }

  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist={
    "id": 4,
    "name": "Guns N Petals",
    "genres": ["Rock n Roll"],
    "city": "San Francisco",
    "state": "CA",
    "phone": "326-123-5000",
    "website": "https://www.gunsnpetalsband.com",
    "facebook_link": "https://www.facebook.com/GunsNPetals",
    "seeking_venue": True,
    "seeking_description": "Looking for shows to perform at in the San Francisco Bay Area!",
    "image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80"
  }
  # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue={
    "id": 1,
    "name": "The Musical Hop",
    "genres": ["Jazz", "Reggae", "Swing", "Classical", "Folk"],
    "address": "1015 Folsom Street",
    "city": "San Francisco",
    "state": "CA",
    "phone": "123-123-1234",
    "website": "https://www.themusicalhop.com",
    "facebook_link": "https://www.facebook.com/TheMusicalHop",
    "seeking_talent": True,
    "seeking_description": "We are on the lookout for a local artist to play every two weeks. Please call us.",
    "image_link": "https://images.unsplash.com/photo-1543900694-133f37abaaa5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=400&q=60"
  }
  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@csrf.exempt
@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@csrf.exempt
@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  form = ArtistForm(request.form)
  if form.validate_on_submit():
    try:
      name = form.name.data
      city = form.city.data
      state = form.state.data
      phone = form.phone.data
      genres = form.genres.data
      website = form.website.data
      facebook_link = form.facebook_link.data
      image_link = form.image_link.data

      artist = Artist(name=name, city=city, state=state, phone=phone, genres=genres, facebook_link=facebook_link, website=website, image_link=image_link)

      db.session.add(artist)
      db.session.commit()

      flash('Artist ' + name + ' was successfully listed!')

    except:
      db.session.rollback()
      print(sys.exc_info())
      flash('An error occurred. Artist ' + form.name.data + ' could not be listed.')

    finally:
      db.session.close()
  else:
    print(form.errors)

  return render_template('pages/home.html')

#  Shows
#  ----------------------------------------------------------------

@csrf.exempt
@app.route('/shows')
def shows():

  data = []
  shows = db.session.query(Show).all()
  for show in shows:
    show_dict = {
      "venue_id": show.venue_id,
      "venue_name": db.session.query(Venue.name).filter_by(id=show.venue_id).all()[0][0],
      "artist_id": show.artist_id,
      "artist_name": db.session.query(Artist.name).filter_by(id=show.artist_id).all()[0][0],
      "artist_image_link": db.session.query(Artist.image_link).filter_by(id=show.artist_id).all()[0][0],
      "start_time": show.start_time.strftime("%m/%d/%Y, %H:%M:%S")
    }
    data.append(show_dict)
  return render_template('pages/shows.html', shows=data)

@csrf.exempt
@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@csrf.exempt
@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  form = ShowForm(request.form)
  if form.validate_on_submit():
    try:
      artist_id = form.artist_id.data
      venue_id = form.venue_id.data
      start_time = form.start_time.data

      show = Show(start_time=start_time, venue_id=venue_id, artist_id=artist_id)

      db.session.add(show)
      db.session.commit()

      # on successful db insert, flash success
      flash('Show was successfully listed!')

    except:
      db.session.rollback()
      print(sys.exc_info())
      flash('An error occurred. Show could not be listed.')

    finally:
      db.session.close()
  else:
    print(form.errors)

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
