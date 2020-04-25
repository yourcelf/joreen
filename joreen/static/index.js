import React, {useState, useEffect, useRef} from 'react';
import ReactDOM from 'react-dom';
import './index.scss';

const TERMS = ['first_name', 'last_name', 'number'];
const humanizeTerm = term => term.replace(/_/g, ' ');

const readSearchParams = function () {
  const params = new URLSearchParams(document.location.search);
  return Object.fromEntries(TERMS.map(term => [term, params.get(term) || '']));
};

const Route = () => {
  if (document.location.pathname === '/') {
    return (
      <App>
        <Search />
      </App>
    );
  } else if (document.location.pathname === '/about/') {
    return (
      <App>
        <About />
      </App>
    );
  }
};

const getMinimumSearchTermsMessage = (minima, searchTerms) => {
  let match = false;
  minima.forEach(termSet => {
    if (termSet.every(term => !!searchTerms[term])) {
      match = true;
    }
  });
  if (match) {
    return null;
  }
  return (
    <>
      {'requires '}
      {minima.map((termSet, j) => (
        <React.Fragment key={`termSet-${j}`}>
          {termSet.map((term, i) => (
            <span key={`term-${j}-${i}`}>
              <i>{humanizeTerm(term)}</i>
              {i < termSet.length - 1 ? ' AND ' : null}
            </span>
          ))}
          {j < minima.length - 1 ? '; or ' : null}
        </React.Fragment>
      ))}
    </>
  );
};

const RESULT_SORT_PREFERENCE = {
  Incarcerated: 1,
  Unknown: 2,
  Released: 3,
};

const Search = () => {
  const [availableStates, setAvailableStates] = useState({});
  const [searchTerms, setSearchTerms] = useState(readSearchParams());
  const [searchResults, setSearchResults] = useState([]);
  const [searchLoading, setSearchLoading] = useState({});
  const [firstLoad, setFirstLoad] = useState(true);

  // Identiy which states lack sufficient search terms
  const belowMinimum = Object.fromEntries(
    Object.entries(availableStates)
      .map(([stateAbbr, stateDetails]) => [
        stateAbbr,
        getMinimumSearchTermsMessage(
          stateDetails.minimum_search_terms,
          searchTerms,
        ),
      ])
      .filter(([stateAbbr, message]) => !!message),
  );

  // Fetch list of available states on load.
  useEffect(() => {
    fetch('/api/states.json')
      .then(res => res.json())
      .then(data => setAvailableStates(data.states));
  }, []);

  // Execute search.  We want to have the latest values of `searchResults` and
  // `searchLoading` available so that as each async fetch comes in, we can
  // append its results.  However, just enclosing those values will result in
  // stale closures[1], preventing us from appending correctly. And we can't
  // just add `searchResults` and `searchLoading` as dependencies for
  // `useEffect`, or the function will execute every time those change.  To get
  // around this, we use `useRef` to obtain an enclosable un-stale reference to
  // which we can assign the latest value for these state vars.
  //
  // [1]: https://dmitripavlutin.com/react-hooks-stale-closures/
  const searchResultsRef = useRef(searchResults);
  searchResultsRef.current = searchResults;
  const searchLoadingRef = useRef(searchLoading);
  searchLoadingRef.current = searchLoading;
  useEffect(() => {
    const hasSearch = TERMS.some(term => !!searchTerms[term]);
    const hasStates = Object.keys(availableStates).length > 0;
    if (!hasStates) {
      return;
    }
    if (hasStates && !hasSearch) {
      if (searchResultsRef.current.length) {
        setSearchResults([]);
      }
      if (Object.keys(searchLoadingRef.current).length) {
        setSearchLoading({});
      }
      return;
    }
    if (hasSearch && hasStates) {
      const params = new URLSearchParams();
      TERMS.forEach(term => params.append(term, searchTerms[term] || ''));
      if (`${params}` !== document.location.search) {
        // Clear previous results
        setSearchResults([]);

        // Mark current search
        history.pushState(
          searchTerms,
          document.title,
          `${window.location.pathname}?${params}`,
        );

        // Set loading state
        const loading = Object.fromEntries(
          Object.keys(availableStates)
            .filter(stateAbbr => !belowMinimum[stateAbbr])
            .map(stateAbbr => [stateAbbr, true]),
        );
        setSearchLoading(loading);

        // Fetch new results
        Object.keys(loading).forEach(stateAbbr => {
          fetch(`/api/search.json?${params}&state=${stateAbbr}`)
            .then(res => res.json())
            .then(data => {
              setSearchLoading({
                ...searchLoadingRef.current,
                [stateAbbr]: false,
              });
              const newResults = [
                ...searchResultsRef.current,
                ...data.results,
              ].sort(
                (a, b) =>
                  RESULT_SORT_PREFERENCE[a.status] -
                  RESULT_SORT_PREFERENCE[b.status],
              );
              setSearchResults(newResults);
              setFirstLoad(false);
            });
        });
      }
    }
  }, [searchTerms, availableStates]);

  return (
    <>
      <StateListHeading states={availableStates} />
      <div>
        <SearchBox searchTerms={searchTerms} onChange={setSearchTerms} />
        <ul className="py-4">
          {Object.entries(availableStates).map(([abbr, details]) =>
            searchLoading[abbr] ? (
              <li key={abbr} className="list-disc list-inside">
                <b>{details.name}</b> <LoadingSpinner />
              </li>
            ) : belowMinimum[abbr] && !firstLoad ? (
              <li key={abbr} className="list-disc list-inside">
                <b>{details.name}</b> {belowMinimum[abbr]}
              </li>
            ) : null,
          )}
        </ul>

        <SearchResults searchResults={searchResults} firstLoad={firstLoad} />
      </div>
    </>
  );
};

const StateListHeading = ({states}) => {
  const nameList = Object.entries(states)
    .filter(([abbr, details]) => abbr !== 'federal')
    .map(([abbr, details]) => details.name);
  nameList.sort();
  nameList.push(`${nameList.length ? 'and ' : ''}in the federal system`);
  return (
    <p className="py-4 text-lg">
      Search for people incarcerated in {nameList.join(', ')}.
    </p>
  );
};

const SearchBox = ({searchTerms, onChange}) => {
  const [firstName, setFirstName] = useState(searchTerms.first_name);
  const [lastName, setLastName] = useState(searchTerms.last_name);
  const [number, setNumber] = useState(searchTerms.number);

  return (
    <form
      onSubmit={e => {
        e.preventDefault();
        onChange({
          first_name: firstName,
          last_name: lastName,
          number: number,
        });
      }}
      className={`
        grid grid-cols-1 col-gap-2
        sm:grid-flow-col sm:grid-cols-4 sm:grid-rows-2-auto
      `}
    >
      <label htmlFor="first-name">First Name</label>
      <input
        id="first-name"
        className="border border-gray-600 p-2"
        type="text"
        value={firstName}
        onChange={e => setFirstName(e.target.value)}
      />

      <label htmlFor="last-name">Last Name</label>
      <input
        id="last-name"
        className="border border-gray-600 p-2"
        type="text"
        value={lastName}
        onChange={e => setLastName(e.target.value)}
      />

      <label htmlFor="last-name">Number</label>
      <input
        id="last-name"
        className="border border-gray-600 p-2"
        type="text"
        value={number}
        onChange={e => setNumber(e.target.value)}
      />

      <span />
      <button type="submit" className="bg-blue-300 py-2 px-4 hover:bg-blue-200">
        Search
      </button>
    </form>
  );
};

const SearchResults = ({searchResults, firstLoad}) => {
  const fmtNumbers = result => {
    const numberEntries = Object.entries(result.numbers);
    return numberEntries
      .map(([type, num]) => {
        if (type && numberEntries.length > 1) {
          return `${humanizeTerm(
            type.toUpperCase().replace('NUMBER', 'Number'),
          )}: ${num}`;
        } else {
          return num;
        }
      })
      .join('; ');
  };
  const getAddresses = function (result) {
    if (result.status === 'Released') {
      return <span></span>;
    } else if (result.facilities.length === 0) {
      return (
        <span className="address-lines">
          {result.raw_facility_name.trim()} (address unknown)
        </span>
      );
    } else if (result.facilities.length === 1) {
      return <Address facility={result.facilities[0]} multiple={false} />;
    } else {
      const addresses = result.facilities.map(facility => {
        return (
          <Address facility={facility} key={facility.id} multiple={true} />
        );
      });
      return (
        <div>
          <h2>
            There are multiple addresses for <em>{result.raw_facility_name}</em>
          </h2>
          {addresses}
        </div>
      );
    }
  };
  const uniqueKey = result =>
    [
      result.administrator_name,
      result.status,
      result.raw_facility_name,
      result.name,
      Object.values(result.numbers).join('-'),
    ].join('-');

  return (
    <div>
      {searchResults.map(result => (
        <div key={uniqueKey(result)} className="mb-6">
          <div>
            <span className='font-lg font-bold pr-2'>{result.name}</span>
            <span className='font-mono'>{fmtNumbers(result)}</span>
          </div>
          <div>
            {result.status === 'Released' ? (
              'Released'
            ) : !result.raw_facility_name ? (
              result.status
            ) : (
              <span>
                Facility: <span>{result.raw_facility_name}</span>
              </span>
            )}
          </div>
          <div className="pl-4 whitespace-pre font-mono">{getAddresses(result)}</div>
          <div className="text-sm">
            Result from{' '}
            {result.search_url ? (
              <a href={result.search_url} className="link">{result.administrator_name}</a>
            ) : (
              result.administrator_name
            )}
          </div>
        </div>
      ))}
    </div>
  );
};

const Address = ({facility, multiple}) => {
  const general = multiple && facility.general;
  return (
    <div className={'address' + (general ? ' general' : '')}>
      {general ? <div className="general-heading">General address</div> : null}
      <div className="address-lines">{facility.formatted_address}</div>
      <div className="provenance" className="text-sm">
        <a href={facility.provenance_url} className="link font-sans">address info</a>
      </div>
    </div>
  );
};

const LoadingSpinner = () => (
  <span>
    <span className="loading-spinner" />
    <span className="sr-only">Loading...</span>
  </span>
);

const About = () => {
  return (
    <div>
      <h1 className="text-4xl py-8">About</h1>
      <p className="mb-4">
        This inmate locator works by directly searching various official inmate
        search tools, to take away some of the hassle and inconsistency of
        finding people who are moved frequently. It was designed with the
        generous support of{' '}
        <a className="link" href="http://www.blackandpink.org/">
          Black and Pink
        </a>{' '}
        for the benefit of organizations that support people in prison.
      </p>
      <p className="mb-4">
        Are you interested in supporting this tool, or helping us to add
        additional states? Please{' '}
        <a className="link" href="mailto:inmatelocator@fohn.org">
          contact us
        </a>
        .
      </p>
    </div>
  );
};

const App = ({children}) => (
  <>
    <div
      className={`
        bg-gray-900 text-white py-4 text-xl
      `}>
      <div className="content-spacing">
        <a href="/" className="pr-6">
          Inmate Locator
        </a>
        <a href="/about/">About</a>
      </div>
    </div>
    <div className="content-spacing">
      <div>{children}</div>
    </div>
  </>
);

const app = ReactDOM.render(<Route />, document.getElementById('app'));
