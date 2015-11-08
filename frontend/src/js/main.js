"use strict";
import _ from 'lodash';
import React from 'react';
import {render} from 'react-dom';
import {Row, Col, Input, Button} from 'react-bootstrap';

import xhr from './xhr.js';
import conf from './conf.js';
import Fa from './fa.jsx';

const humanizeKey = function(key) {
  return key.replace(/_/g, " ");
}

const checkMinimumSearchTerms = function(minima, searchTerms) {
  for (var i = 0; i < minima.length; i++) {
    let allTerms = _.map(minima[i], (val) => !!searchTerms[val]);
    if (_.all(allTerms)) {
      return;
    }
  }
  let minimaDescr = [];
  _.each(minima, (minimum, j) => {
    let terms = _.sortBy(minimum);
    _.each(terms, (term, i) => {
      minimaDescr.push(<i key={"term-" + term}>{humanizeKey(term)}</i>);
      if (i < minimum.length - 1) {
        minimaDescr.push(<span key={`and-${j}-${i}`}> AND </span>)
      }
    });
    if (j < minima.length - 1) {
      minimaDescr.push(<span key={`or-${j}`}>, or </span>);
    }
  });
  return <span>requires either {minimaDescr}</span>
};

const readQueryargs = function() {
  let urlParams;
  let match,
      pl     = /\+/g,  // Regex for replacing addition symbol with a space
      search = /([^&=]+)=?([^&]*)/g,
      decode = function (s) { return decodeURIComponent(s.replace(pl, " ")); },
      query  = window.location.search.substring(1);

  urlParams = {};
  while (match = search.exec(query)) {
     urlParams[decode(match[1])] = decode(match[2]);
  }
  return {
    first_name: urlParams.first_name || '',
    last_name: urlParams.last_name || '',
    number: urlParams.number || ''
  };
};

const pushQueryargs = function(terms) {
  let urlParams = readQueryargs();
  let changed = false;
  _.each(terms, function(val, key) {
    if (urlParams[key] !== val) {
      urlParams[key] = val;
      changed = true;
    }
  });
  if (changed === true && typeof history !== "undefined") {
    let querystr;
    if (!_.some(terms)) {
      querystr = ""
    } else {
      querystr = "?" + _.map(urlParams, (val, key) => {
        return `${encodeURIComponent(key)}=${encodeURIComponent(val)}`
      }).join("&");
    }

    let url = [
      window.location.protocol,
      "//",
      window.location.host,
      window.location.pathname,
      querystr
    ].join("");
    history.pushState(null, "", url);
  }
};

const App = React.createClass({
  getInitialState() {
    let queryargs = readQueryargs();
    return {
      states: {},
      searchTerms: queryargs,
      searchResults: [],
      searchesLoading: {},
      firstLoad: true
    };
  },
  componentWillMount() {
    xhr.get(conf.statesUrl).then((data) => {
      this.setState({states: data.states});
      // Set up onpopstate
      window.onpopstate = () => {
        let urlParams = readQueryargs()
        this.setState({
          searchTerms: urlParams
        });
        window.setTimeout(() => this.doSearch(), 1);
      };
      // Execute first search if we have params.
      let urlParams = readQueryargs();
      if (_.any(urlParams)) {
        window.onpopstate();
      }
    });
  },
  handleChangeSearchTerms(searchTerms) {
    this.setState({searchTerms: searchTerms});
  },
  doSearch() {
    pushQueryargs(this.state.searchTerms);
    this.setState({searchResults: []});
    let loading = {};
    _.each(this.state.states, (details, abbr) => {
      let minimaError = checkMinimumSearchTerms(details.minimum_search_terms, this.state.searchTerms);
      if (minimaError) {
        loading[abbr] = {
          state: details,
          error: minimaError
        };
      } else {
        loading[abbr] = {state: details};
        let terms = _.clone(this.state.searchTerms);
        terms.state = abbr;
        xhr.get(conf.searchUrl, terms).then((res) => {
          let loading = _.clone(this.state.searchesLoading);
          delete loading[abbr];
          let sortedResults = _.sortBy(this.state.searchResults.concat(res.results), (result) => {
            return {
              "Incarcerated": 1,
              "Unknown": 2,
              "Released": 3,
            }[result.status];
          });
          this.setState({
            searchesLoading: loading,
            searchResults: sortedResults,
            firstLoad: false
          });
        }).catch((err) => {
          console.log("XHR GET error", abbr, err, this.state.searchesLoading);
          let loading = _.clone(this.state.searchesLoading);
          if (!loading[abbr]) { loading[abbr] = {}; }
          loading[abbr].error = err.error;
          this.setState({searchesLoading: loading});
        });
      }
    });
    this.setState({searchesLoading: loading});
  },
  render() {
    let stateList = [];
    _.each(this.state.states, (details, abbr) => {
      if (abbr !== "federal") {
        stateList.push(details.name);
      }
    });
    stateList.sort();
    if (stateList.length) {
      stateList.push("and in the federal system");
    } else {
      stateList.push("in the federal system");
    }
    return (
      <div>
        <Col xs={12} sm={7}>
          <h1>Inmate Locator</h1>
          <p>Search for people incarcerated in <span>{stateList.join(", ")}</span>.</p>
        </Col>
        <Col xs={12}>
          <SearchBox searchTerms={this.state.searchTerms}
                    handleChange={this.handleChangeSearchTerms}
                    doSearch={this.doSearch} />
        </Col>
        <Col xs={12}>
          <SearchesLoading searchesLoading={this.state.searchesLoading} />
        </Col>
        <Col xs={12}>
          <SearchResultList searchResults={this.state.searchResults}
                            firstLoad={this.state.firstLoad}
                            />
        </Col>
      </div>
    );
  }
});

const SearchBox = React.createClass({
  handleChange() {
    this.props.handleChange({
      first_name: this.refs.first.getValue(),
      last_name: this.refs.last.getValue(),
      number: this.refs.number.getValue()
    });
  },
  handleSubmit(event) {
    event.preventDefault()
    this.props.doSearch();
  },
  render() {
    return (
      <form className='form-inline' onSubmit={this.handleSubmit}>
        <Input type='search' onChange={this.handleChange}
          placeholder="First name" ref="first" value={this.props.searchTerms.first_name} />
        <Input type='search' onChange={this.handleChange}
          placeholder="Last name" ref="last" value={this.props.searchTerms.last_name} />
        <Input type='search' onChange={this.handleChange}
          placeholder="Assigned number" ref="number" value={this.props.searchTerms.number} />
        <Button bsStyle='primary' type='submit'><Fa type='search' alt='Search' /></Button>
      </form>
    );
  }
});

const Address = React.createClass({
  render() {
    let general = this.props.multiple && this.props.facility.general;
    return (
      <div className={'address' + (general ? ' general' : '')}>
        {
          this.props.multiple && this.props.facility.general ?
          <div className='general-heading'>General address</div>
          : ""
        }
        <div className='address-lines'>{this.props.facility.formatted_address}</div>
        <div className='provenance'><a href={this.props.facility.provenance_url}>address info</a></div>
      </div>
    );
  }
});

const SearchResultList = React.createClass({
  render() {
    if (this.props.firstLoad) {
      return <span></span>
    }
    if (this.props.searchResults.length === 0) {
      return <p>No results</p>
    }
    let fmtKey = (result) => [
      result.administrator_name, result.status,
      result.raw_facility_name, result.name,
      _.values(result.numbers).join("-")
    ].join("-");

    let fmtNumbers = (result) => {
      return _.map(result.numbers, (num, type) => {
        if (type && _.size(result.numbers) > 1) {
          return `${humanizeKey(type.toUpperCase().replace("NUMBER", "Number"))}: ${num}` 
        } else {
          return num;
        }
      }).join("; ")
    };

    let getAddresses = function(result) {
      if (result.status === "Released") {
        return <span></span>;
      } else if (result.facilities.length === 0) {
        return <span className='address-lines'>{result.raw_facility_name} (address unknown)</span>
      } else if (result.facilities.length === 1) {
        return <Address facility={result.facilities[0]} multiple={false} />
      } else {
        let addresses = _.map(result.facilities, (facility) => {
          return <Address facility={facility} key={facility.id} multiple={true} />
        });
        return (
          <div>
            <h2>There are multiple addresses for <em>{result.raw_facility_name}</em></h2>
            { addresses }
          </div>
        );
      }
    };

    let results = _.map(this.props.searchResults, (result) => (
      <div className='result' key={fmtKey(result)}>
        <div>
          <span className='name'>{result.name}</span>,{' '}
          <span className='numbers'>{fmtNumbers(result)}</span>
        </div>
        <div className='status'>
          {result.status === "Released" ? "Released" :
           !result.raw_facility_name ? result.status : <span>
            Facility: <span className='raw-facility'>{result.raw_facility_name}</span>
          </span>}
        </div>
        <div className='addresses'>{ getAddresses(result) }</div>
        <div className='provenance'>
          Result from{' '}
          { result.search_url ?
            <a href={result.search_url}>{result.administrator_name}</a> :
            result.administrator_name}{'. '}
        </div>
      </div>
    ));
    return (
      <div className='searchResults'>
        {results}
      </div>
    )
  }
});

const SearchesLoading = React.createClass({
  render() {
    if (_.size(this.props.searchesLoading) === 0) {
      return <span></span>;
    }
    let loading = [];
    _.each(this.props.searchesLoading, (details, abbr) => {
      if (details.error) {
        loading.push(
          <li className='error' key={"loading-" + abbr}>
            <strong>{details && details.state && details.state.name || abbr}</strong>
            {' '}{details.error}
          </li>
        );
      } else {
        loading.push(
          <li key={"loading-" + abbr}>
            <strong>{details && details.state && details.state.name || abbr}</strong>
            {' '}<Fa type='spinner spin' alt='loading'/>
          </li>
        );
      }
    });
    return (
      <ul>{loading}</ul>
    )
  }
});


const app = render(<App searchTerms={{}} searchResults={{}} searchesLoading={{}} />,
                   document.getElementById('app'));
