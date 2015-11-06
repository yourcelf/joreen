"use strict";
import _ from 'lodash';
import React from 'react';
import {render} from 'react-dom';
import {Row, Col, Input, Button} from 'react-bootstrap';

import xhr from './xhr.js';
import conf from './conf.js';
import Fa from './fa.jsx';

const App = React.createClass({
  getInitialState() {
    return {
      states: {},
      searchTerms: {first: '', last: '', number: ''},
      searchResults: [],
      searchesLoading: []
    };
  },
  componentWillMount() {
    xhr.get(conf.statesUrl).then((data) => {
      console.log(data);
      this.setState({states: data.states});
    });
  },
  handleChangeSearchTerms(searchTerms) {
    this.setState({searchTerms: searchTerms});
    
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
      stateList.push("and anywhere in the federal system");
    } else {
      stateList.push("anywhere in the federal system");
    }
    return (
      <div>
        <Col xs={12} sm={6}>
          <h1>Inmate Locator</h1>
          <p>Search for people incarcerated in <span>{stateList.join(", ")}</span>.</p>
        </Col>
        <Col xs={12}>
          <SearchBox searchTerms={this.state.searchTerms}
                    handleChange={this.handleChangeSearchTerms} />
        </Col>
        <Col xs={12}>
          <SearchesLoading searchesLoading={this.state.searchesLoading} />
        </Col>
        <Col xs={12}>
          <SearchResults searchResults={this.state.searchResults}
                         searchTerms={this.state.searchTerms}
                         searchesLoading={this.state.searchesLoading} />
        </Col>
      </div>
    );
  }
});

const SearchBox = React.createClass({
  handleChange() {
    this.props.handleChange({
      first: this.refs.first.getValue(),
      last: this.refs.last.getValue(),
      number: this.refs.number.getValue()
    });
  },
  render() {
    return (
      <form className='form-inline'>
        <Input type='search' onChange={this.handleChange}
          placeholder="First name" ref="first" value={this.props.searchTerms.first} />
        <Input type='search' onChange={this.handleChange}
          placeholder="Last name" ref="last" value={this.props.searchTerms.last} />
        <Input type='search' onChange={this.handleChange}
          placeholder="Assigned number" ref="number" value={this.props.searchTerms.number} />
        <Button bsStyle='primary'><Fa type='search' alt='Search' /></Button>
      </form>
    );
  }
});

const SearchResults = React.createClass({
  render() {
    let hasSearch = (this.props.searchTerms && (
      this.props.searchTerms.first ||
      this.props.searchTerms.last ||
      this.props.searchTerms.number
    ));
    if (!hasSearch) {
      return <span></span>
    }
    if (this.props.searchResults.length === 0 &&
        this.props.searchesLoading.length === 0) {
      return <p>No results</p>
    }
    return (
      <pre>{JSON.stringify(this.props.searchResults)}</pre>
    )
  }
});

const SearchesLoading = React.createClass({
  render() {
    if (this.props.searchesLoading.length === 0) {
      return <span></span>;
    }
    return (
      <pre>Loading: {JSON.stringify(this.props.searchesLoading)}</pre>
    )
  }
});


const app = render(<App searchTerms={{}} searchResults={{}} searchesLoading={{}} />,
                   document.getElementById('app'));
