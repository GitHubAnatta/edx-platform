;(function (define) {

define(['backbone'], function(Backbone) {
    'use strict';

    return function (Collection, Form, ResultListView, searchQuery) {

        var collection = new Collection([]);
        var results = new ResultListView({ collection: collection });
        var dispatcher = _.clone(Backbone.Events);
        var form = new Form();

        dispatcher.listenTo(form, 'search', function (query) {
            collection.performSearch(query);
            form.showLoadingIndicator();
        });

        dispatcher.listenTo(form, 'clear', function () {
            results.clearResults();
        });

        dispatcher.listenTo(results, 'next', function () {
            collection.loadNextPage();
            form.showLoadingIndicator();
        });

        dispatcher.listenTo(collection, 'search', function () {
            if (collection.length > 0) {
                results.render();
            }
            else {
                form.showNotFoundMessage(collection.searchTerm);
            }
            form.hideLoadingIndicator();
        });

        dispatcher.listenTo(collection, 'next', function () {
            results.renderNext();
            form.hideLoadingIndicator();
        });

        dispatcher.listenTo(collection, 'error', function () {
            form.showErrorMessage();
            form.hideLoadingIndicator();
        });


        // kick off search if URL contains ?search_query=
        if (searchQuery) {
            form.doSearch(searchQuery);
        }

    };

});

})(define || RequireJS.define);
