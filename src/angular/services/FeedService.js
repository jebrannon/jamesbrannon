'use strict';

var FeedService = function ($http, $q, Utils) {
	
	//  Items array to hold list of all story items
	var _items = [];
	var _network = {
		'blogger': 'https://www.googleapis.com/blogger/v3/blogs/{user}/posts?key={key}&fields=items(title,id,published,url,content)&maxResults={limit}&callback=JSON_CALLBACK'
	};

	/*
		Public methods
	*/
	this.get = function (id) {
		console.log('GET', id);
	};
	this.load = function (params) {
		var _url = Utils.formatString(_network[params.type], {
			user: params.user,
			key: params.key,
			limit: params.limit
		});
		var	_deferred = $q.defer();

		//  Action request
		$http.jsonp(_url).
			success(function(response) {
				_deferred.resolve(_handleResponse({'type': params.type, 'resp': response}));
			}).
			error(function(response) {
				_deferred.reject(response);
			});
		return _deferred.promise;
	};

	/*
		Private methods
	*/
	var _handleResponse = function (data) {
		switch(data.type) {
			case 'blogger':
				return _parseBloggerFeed(data.resp);
			case 'twitter':
				break;
		}
	};
	var _parseBloggerFeed = function (response) {
		var _items = [];
		var _len = response.items.length;
		var _inc = 0;
		var _o = {};
		var _item;
		while (_len--) {
			_item = response.items[_inc];
			_o = _formatItemObject({
				title: _item.title,
				body: Utils.stripHTML(_item.content),
				images: Utils.getImagesFromString(_item.content),
				published: Utils.formatDateString(_item.published),
				link: _item.url
			});

			//  Add item to items array
			_items.push(_o);
			_inc++;
		}
		return {'items': _items};
	};
	var _formatItemObject = function (data) {
		var _o = {};
		if (data.title && data.title.length) { _o.title = data.title; }
		if (data.body && data.body.length) { _o.body = data.body; }
		if (data.images && data.images.length) { _o.images = data.images; }
		if (data.published && data.published.length) { _o.published = data.published; }
		if (data.link && data.link.length) { _o.link = data.link; }
		return _o;
	};
};
module.exports = FeedService;
