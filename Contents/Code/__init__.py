TITLE = 'NPO'
API_BASE_URL = 'https://apps-api.uitzendinggemist.nl'
EPISODE_URL = 'https://www.npo.nl/redirect/00-00-0000/%s'
DAY = ['Maandag', 'Dinsdag', 'Woensdag', 'Donderdag', 'Vrijdag', 'Zaterdag', 'Zondag']
MONTH = ['', 'januari', 'februari', 'maart', 'april', 'mei', 'juni', 'juli', 'augustus', 'september', 'oktober', 'november', 'december']

####################################################################################################
def Start():

	ObjectContainer.title1 = TITLE
	HTTP.CacheTime = 300
	HTTP.Headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.116 Safari/537.36'

####################################################################################################
@handler('/video/npo', TITLE)
def MainMenu(**kwargs):

	oc = ObjectContainer()

#	oc.add(DirectoryObject(key=Callback(Overview, title='Kijktips', path='tips.json'), title='Kijktips'))
	oc.add(DirectoryObject(key=Callback(Overview, title='Populair', path='episodes/popular.json'), title='Populair'))
	oc.add(DirectoryObject(key=Callback(Overview, title='Meest bekeken', path='episodes/trending.json'), title='Meest bekeken'))
	oc.add(DirectoryObject(key=Callback(OnDemand), title='Gemist'))
	oc.add(DirectoryObject(key=Callback(AZ), title='Programma\'s A-Z'))

	return oc

####################################################################################################
@route('/video/npo/overview')
def Overview(title, path, **kwargs):

	oc = ObjectContainer(title2=title)
	json_obj = JSON.ObjectFromURL('%s/%s' % (API_BASE_URL, path))
	episodes = []

	for video in json_obj:

		if 'episodes/' in path: # Populair en Meest bekeken

			title = '%s - %s' % (video['series']['name'], video['name']) if video['name'] != "" else video['series']['name']
			summary = video['description']
			episode_id = video['mid']

			thumbs = []
			if video['image']: thumbs.append(video['image'])
			if 'stills' in video and video['stills']: thumbs.append(video['stills'][0]['url'])
			if video['series']['image']: thumbs.append(video['series']['image'])

			broadcasted_at = video['broadcasted_at']

		elif 'broadcasts/' in path: # Gemist

			title = '%s - %s' % (video['episode']['series']['name'], video['episode']['name']) if video['episode']['series']['name'].lower() not in video['episode']['name'].lower() else video['episode']['name']
			title = title.strip(' -')
			summary = video['episode']['description']
			episode_id = video['episode']['mid']

			thumbs = []
			if video['episode']['image']: thumbs.append(video['episode']['image'])
			if 'stills' in video['episode'] and video['episode']['stills']: thumbs.append(video['episode']['stills'][0]['url'])
			if video['episode']['series']['image']: thumbs.append(video['episode']['series']['image'])

			broadcasted_at = video['episode']['broadcasted_at']

		else: # Kijktips

			title = '%s - %s' % (video['episode']['series']['name'], video['name']) if video['episode']['series']['name'].lower() not in video['name'].lower() else video['name']
			summary = video['description']
			episode_id = video['episode']['mid']

			thumbs = []
			if video['episode']['image']: thumbs.append(video['episode']['image'])
			if 'stills' in video['episode'] and video['episode']['stills']: thumbs.append(video['episode']['stills'][0]['url'])
			if video['episode']['series']['image']: thumbs.append(video['episode']['series']['image'])

			broadcasted_at = video['episode']['broadcasted_at']

		episodes.append({
			'episode_id': episode_id,
			'title': title,
			'summary': summary,
			'thumbs': thumbs,
			'broadcasted_at': broadcasted_at
		})

	episodes = sorted(episodes, key=lambda k: k['broadcasted_at'], reverse=True)

	for episode in episodes:

		oc.add(DirectoryObject(
			key = Callback(Episode, episode_id=episode['episode_id']),
			title = episode['title'],
			summary = episode['summary'],
			thumb = Resource.ContentsOfURLWithFallback(episode['thumbs'])
		))

	return oc

####################################################################################################
@route('/video/npo/episode/{episode_id}')
def Episode(episode_id, **kwargs):

	video = JSON.ObjectFromURL('%s/episodes/%s.json' % (API_BASE_URL, episode_id))

	oc = ObjectContainer(title2=video['series']['name'])

	airdate = Datetime.FromTimestamp(video['broadcasted_at'])
	title = video['name'] if video['name'] else video['series']['name']
	title = '%s (%s %s %s)' % (title, airdate.day, MONTH[airdate.month], airdate.year)

	thumbs = []
	if video['image']: thumbs.append(video['image'])
	if 'stills' in video and video['stills']: thumbs.append(video['stills'][0]['url'])
	if video['series']['image']: thumbs.append(video['series']['image'])

	oc.add(VideoClipObject(
		url = EPISODE_URL % (video['mid']),
		title = title,
		summary = video['description'],
		duration = video['duration'] * 1000,
		originally_available_at = airdate.date(),
		thumb = Resource.ContentsOfURLWithFallback(thumbs)
	))

	oc.add(DirectoryObject(
		key = Callback(Series, series_id=video['series']['id']),
		title = 'Alle afleveringen'
	))

	return oc

####################################################################################################
@route('/video/npo/series/{series_id}')
def Series(series_id, **kwargs):

	json_obj = JSON.ObjectFromURL('%s/series/%s.json' % (API_BASE_URL, series_id))

	oc = ObjectContainer(title2=json_obj['name'])

	for video in json_obj['episodes']:

		airdate = Datetime.FromTimestamp(video['broadcasted_at'])
		title = video['name'] if video['name'] else json_obj['name']
		title = '%s (%s %s %s)' % (title, airdate.day, MONTH[airdate.month], airdate.year)

		thumbs = []
		if video['image']: thumbs.append(video['image'])
		if 'stills' in video and video['stills']: thumbs.append(video['stills'][0]['url'])
		if json_obj['image']: thumbs.append(json_obj['image'])

		oc.add(VideoClipObject(
			url = EPISODE_URL % (video['mid']),
			title = title,
			summary = video['description'],
			duration = video['duration'] * 1000,
			originally_available_at = airdate.date(),
			thumb = Resource.ContentsOfURLWithFallback(thumbs)
		))

	return oc

####################################################################################################
@route('/video/npo/ondemand')
def OnDemand(**kwargs):

	oc = ObjectContainer(title2='Gemist')
	delta = Datetime.Delta(days=1)
	yesterday = (Datetime.Now() - delta).date()

	oc.add(DirectoryObject(key=Callback(Overview, title='Laatst toegevoegd', path='broadcasts/recent.json'), title='Laatst toegevoegd'))
	oc.add(DirectoryObject(key=Callback(Overview, title='Gisteren', path='broadcasts/%s.json' % (yesterday)), title='Gisteren'))

	for i in range(2, 10):

		date_object = Datetime.Now() - (delta * i)
		title = '%s %s %s' % (DAY[date_object.weekday()], date_object.day, MONTH[date_object.month])

		oc.add(DirectoryObject(key=Callback(Overview, title=title, path='broadcasts/%s.json' % (date_object.date())), title=title))

	return oc

####################################################################################################
@route('/video/npo/az')
def AZ(**kwargs):

	oc = ObjectContainer(title2='Programma\'s A-Z')

	json_obj = JSON.ObjectFromURL('%s/series.json' % (API_BASE_URL))

	for programme in json_obj:

		oc.add(DirectoryObject(
			key = Callback(Series, series_id=programme['mid']),
			title = programme['name'],
			summary = programme['description'],
			thumb = Resource.ContentsOfURLWithFallback(programme['image'])
		))

	return oc
