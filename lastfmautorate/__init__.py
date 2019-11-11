PLUGIN_NAME = 'LastFM AutoRate'
PLUGIN_AUTHOR = 'ZHANKODI'
PLUGIN_DESCRIPTION = '''Use LastFM to automatically rate your music library.'''
PLUGIN_VERSION = "0.1"
PLUGIN_API_VERSIONS = ["0.15"]


from PyQt4 import QtCore
from picard.metadata import register_track_metadata_processor
import urllib
from urllib import urlencode
import re
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

LASTFM_HOST = "ws.audioscrobbler.com"
LASTFM_PORT = 80
LASTFM_KEY = "0a8b8f968b285654f9b4f16e8e33f2ee"
LASTFM_PATH = "/2.0"

_feat_re = re.compile(r"([\s\S]+) feat\.([\s\S]+)", re.IGNORECASE)

def process_track(album, metadata, release, track):
	artist = metadata["albumartist"]
	track = metadata["title"]
	trackwithfeat = track
	
	match = _feat_re.match(metadata["artist"])
	if match:
		metadata["artist"] = match.group(1)
		trackwithfeat = track + " (feat.%s)" % match.group(2)
		
	# Yes, that's right, Last.fm prefers double URL-encoding
	s = urlencode({'artist': artist})
	s = s.split('=')[1]
	
	# Yes, that's right, Last.fm prefers double URL-encoding
	t = urlencode({'track': track})
	t = t.split('=')[1]
	
	twf = urlencode({'track': trackwithfeat})
	twf = twf.split('=')[1]
	
	artistpath = 'http://' + LASTFM_HOST + LASTFM_PATH + '/?method=artist.getinfo&artist=' + s + '&api_key=' + LASTFM_KEY
	artisturl = urllib.urlopen(artistpath)

	artistsite = artisturl.read()
	ArtistListeners = float(re.search('<listeners>(\d+)', artistsite).group(1))
	ArtistPlaycount = float(re.search('<playcount>(\d+)', artistsite).group(1))

	trackpath = 'http://' + LASTFM_HOST + LASTFM_PATH + '/?method=track.getInfo&api_key=' + LASTFM_KEY + '&artist=' + s + '&track=' + t
	trackurl = urllib.urlopen(trackpath)
	tracksite = trackurl.read().decode('utf-8')
	TrackListeners = float(re.search('<listeners>(\d+)', tracksite).group(1))
	TrackPlaycount = float(re.search('<playcount>(\d+)', tracksite).group(1))

	trackwithfeatpath = 'http://' + LASTFM_HOST + LASTFM_PATH + '/?method=track.getInfo&api_key=' + LASTFM_KEY + '&artist=' + s + '&track=' + twf
	trackwithfeaturl = urllib.urlopen(trackwithfeatpath)
	trackwithfeatsite = trackwithfeaturl.read().decode('utf-8')
	TrackWithFeatListeners = float(re.search('<listeners>(\d+)', trackwithfeatsite).group(1))
	TrackWithFeatPlaycount = float(re.search('<playcount>(\d+)', trackwithfeatsite).group(1))

	if TrackWithFeatPlaycount > TrackPlaycount:
		TrackListeners = TrackWithFeatListeners
		TrackPlaycount = TrackWithFeatPlaycount
	

	calc_track_rating(metadata, ArtistListeners, TrackPlaycount, TrackListeners)

def calc_track_rating(metadata, ArtistListeners, TrackPlaycount, TrackListeners):
	TL_AL = TrackListeners / ArtistListeners
	TP_TL = TrackPlaycount / TrackListeners
	
	TL_AL_Weight = 2.5
	TP_TL_Weight = 1.5
	TL_Weight = 1
	
	TL_AL_Max = 0.15
	TP_TL_Max = 5
	TL_Max = 100000
	
	if (TL_AL > TL_AL_Max):
		TL_AL_Score = TL_AL_Weight
	else:
		TL_AL_Score = TL_AL_Weight * (TL_AL / TL_AL_Max)

	if (TP_TL > TP_TL_Max):
		TP_TL_Score = TP_TL_Weight
	else:
		TP_TL_Score = TP_TL_Weight * (TP_TL / TP_TL_Max)		
	
	if (TrackListeners > TL_Max):
		TL_Score = TL_Weight
	else:
		TL_Score = TL_Weight * (TrackListeners / TL_Max)

	Rating = round(TL_AL_Score + TP_TL_Score + TL_Score,0)
	
	metadata["~rating"] = int(Rating)
	
register_track_metadata_processor(process_track)