"use strict";
import React from 'react';

const Fa = React.createClass({
  render() {
    let classes = this.props.type.split(" ").map((t) => "fa-" + t).join(" ");;
    let className = `fa ${classes}`;
    let alt = this.props.alt ? <span className='sr-only'>{this.props.alt}</span> : "";
    return <span><i className={className} />{alt}</span>;
  }
});

export default Fa;
