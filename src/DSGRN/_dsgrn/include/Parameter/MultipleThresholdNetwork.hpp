/// MultipleThresholdNetwork.hpp
/// Shaun Harker
/// 2015-05-22
///
/// Marcio Gameiro
/// 2021-01-02
///
/// Adam Zheleznyak
/// 2021-02-19

#pragma once

#ifndef INLINE_IF_HEADER_ONLY
#define INLINE_IF_HEADER_ONLY
#endif

#include "MultipleThresholdNetwork.h"

INLINE_IF_HEADER_ONLY MultipleThresholdNetwork::
MultipleThresholdNetwork ( void ) { 
  data_ . reset ( new MultipleThresholdNetwork_ );
}

INLINE_IF_HEADER_ONLY MultipleThresholdNetwork::
MultipleThresholdNetwork ( std::string const& s ) {
  assign(s);
}

INLINE_IF_HEADER_ONLY void MultipleThresholdNetwork::
assign ( std::string const& s ) {
  auto colon = s.find(':');
  if ( colon != std::string::npos ) {
    data_ . reset ( new MultipleThresholdNetwork_ );
    data_ -> specification_ = s;
    _parse ( _lines () );
  } else {
    load(s);
  }
}

INLINE_IF_HEADER_ONLY void MultipleThresholdNetwork::
load ( std::string const& filename ) {
data_ . reset ( new MultipleThresholdNetwork_ );
  std::ifstream infile ( filename );
  if ( not infile . good () ) { 
    throw std::runtime_error ( "Problem loading network specification file " + filename );
  }
  std::string line;
  while ( std::getline ( infile, line ) ) {
    data_ -> specification_ += line + '\n';
  }
  infile . close ();
  _parse ( _lines () );
}

INLINE_IF_HEADER_ONLY Network const& MultipleThresholdNetwork::
helper_network ( void ) const {
  return data_ -> helper_network_;
}

INLINE_IF_HEADER_ONLY uint64_t MultipleThresholdNetwork::
size ( void ) const {
  return data_ ->  name_by_index_ . size ();
}

INLINE_IF_HEADER_ONLY uint64_t MultipleThresholdNetwork::
index ( std::string const& name ) const {
  return data_ ->  index_by_name_ . find ( name ) -> second;
}

INLINE_IF_HEADER_ONLY std::string const& MultipleThresholdNetwork::
name ( uint64_t index ) const {
  return data_ ->  name_by_index_[index];
}

INLINE_IF_HEADER_ONLY std::vector<uint64_t> const& MultipleThresholdNetwork:: 
inputs ( uint64_t index ) const {
  return data_ ->  inputs_[index];
}

INLINE_IF_HEADER_ONLY std::vector<uint64_t> const& MultipleThresholdNetwork:: 
outputs ( uint64_t index ) const {
  return data_ ->  outputs_[index];
}

INLINE_IF_HEADER_ONLY std::vector<std::vector<uint64_t>> const& MultipleThresholdNetwork::
logic ( uint64_t index ) const {
  return data_ ->  logic_by_index_ [ index ];
}

INLINE_IF_HEADER_ONLY bool MultipleThresholdNetwork::
essential ( uint64_t index ) const {
  return data_ -> essential_ [ index ];
}

INLINE_IF_HEADER_ONLY std::vector<bool> MultipleThresholdNetwork::
interaction ( uint64_t source, uint64_t target ) const {
  return data_ ->  edge_type_ . find ( std::make_pair ( source, target ) ) -> second;
}

INLINE_IF_HEADER_ONLY uint64_t MultipleThresholdNetwork::
order ( uint64_t source, uint64_t target ) const {
  return data_ -> order_ . find ( std::make_tuple (source, target) ) -> second;
}

//INLINE_IF_HEADER_ONLY uint64_t MultipleThresholdNetwork::
//order ( uint64_t source, uint64_t target, uint64_t instance ) const {
//  return data_ -> order_ . find ( std::make_tuple (source, target, instance) ) -> second;
//}

INLINE_IF_HEADER_ONLY  std::vector<uint64_t> MultipleThresholdNetwork::
domains ( void ) const {
  std::vector<uint64_t> result;
  for ( uint64_t d = 0; d < size(); d++ ) {
    result . push_back ( data_ -> helper_network_ . outputs(d) . size () + 1);
  }
  return result;
}

INLINE_IF_HEADER_ONLY std::string MultipleThresholdNetwork::
specification ( void ) const {
  return data_ -> specification_;
}

INLINE_IF_HEADER_ONLY std::string MultipleThresholdNetwork::
graphviz ( std::vector<std::string> const& theme ) const {
  std::stringstream result;
  // std::cout << "graphviz. Looping through nodes.\n";
  result << "digraph {\n";
  result << "bgcolor = " << theme[0] << ";";
  for ( uint64_t i = 0; i < size (); ++ i ) {
    result << "\"" << name(i) << "\"" << " [style=filled fillcolor=" << theme[1] << "];\n";
  }
  std::string normalhead ("normal");
  std::string blunthead ("tee");
  // std::cout << "graphviz. Looping through edges.\n";
  for ( uint64_t target = 0; target < size (); ++ target ) {
    std::vector<std::vector<uint64_t>> logic_struct = logic ( target );
    std::reverse ( logic_struct . begin (), logic_struct . end () ); // prefer black
    uint64_t partnum = 0;
    for ( auto const& part : logic_struct ) {
      for ( uint64_t source : part ) {
        // std::cout << "Checking type of edge from " << source << " to " << target << "\n";
        if ( interaction(source, target).size() == 1 ) {
          std::string head = ( interaction(source,target)[0] ) ? normalhead : blunthead;
          result << "\"" << name(source) << "\" -> \"" << name(target) << "\" [color=" << theme[partnum+2] << " arrowhead=\"" << head << "\"";
        } else {
          std::string label;
          bool has_activating = false;
          bool has_repressing = false;
          for ( auto const& sign : interaction(source, target) ) {
            if (sign) {
              label += "+";
              has_activating = true;
            } else {
              label += "-";
              has_repressing = true;
            }
          }
          if (has_activating && !has_repressing) {
            result << "\"" << name(source) << "\" -> \"" << name(target) << "\" [color=" << theme[partnum+2] << " arrowhead=\"" << normalhead << "\"";
            result << " label=\"[" << interaction(source, target).size() << "]\"";
          } else if (!has_activating && has_repressing) {
            result << "\"" << name(source) << "\" -> \"" << name(target) << "\" [color=" << theme[partnum+2] << " arrowhead=\"" << blunthead << "\"";
            result << " label=\"[" << interaction(source, target).size() << "]\"";
          } else {
            result << "\"" << name(source) << "\" -> \"" << name(target) << "\" [color=" << theme[partnum+2] << " arrowhead=\"" << normalhead << "\"";
            result << " label=\"[" << label << "]\"";
          }
        }
        result << "];\n";
      }
      ++ partnum;
      if ( partnum + 2 == theme . size () ) partnum = 0;
    }
  }  
  result << "}\n";
  return result . str ();
}

/// _lines
///   Open the network file and read it line by line
INLINE_IF_HEADER_ONLY std::vector<std::string> MultipleThresholdNetwork::
_lines ( void ) {
  // Remove quote marks if they exist, and convert "\n" substrings to newlines
  std::string & str = data_ -> specification_;
  const std::regex quote_regex("\"", std::regex::basic);
  const std::regex newline_regex("\n", std::regex::basic);
  data_ -> specification_ = std::regex_replace(data_ -> specification_, newline_regex, "\n" );
  data_ -> specification_ = std::regex_replace(data_ -> specification_, quote_regex, "" );

  // Parse the lines
  std::vector<std::string> result;
  std::stringstream spec ( data_ -> specification_ );
  std::string line;
  while ( std::getline ( spec, line ) ) {
    result . push_back ( line );
  }
  return result;
}

/// parse
///   Iterate through lines and produce data structures
INLINE_IF_HEADER_ONLY void MultipleThresholdNetwork::
_parse ( std::vector<std::string> const& lines ) {
  using namespace DSGRN_parse_tools;
  std::vector<std::string> logic_strings;
  std::map<std::string, bool> essential_nodes;
  //std::vector<std::string> constraint_strings;
  // Learn the node names
  for ( auto const& line : lines ) {
    auto splitline = split ( line, ':' );
    if ( splitline . empty () ) continue;
    removeSpace(splitline[0]);
    // If begins with . or @, skip
    if ( (splitline[0][0] == '.') || (splitline[0][0] == '@' ) ) continue; 
    data_ -> name_by_index_ . push_back ( splitline[0] );
    // If no logic specified, zero inputs.
    if ( splitline . size () < 2 ) {
      logic_strings . push_back ( " " );
    } else {
      logic_strings . push_back ( splitline[1] );
    }
    //std::cout << line << " has " << splitline.size() << " parts.\n";
    if ( splitline . size () >= 3 ) {
      // TODO: make it check for keyword "essential"
      essential_nodes [ splitline[0] ] = true;
      //std::cout << "Marking " << splitline[0] << " as essential \n";
    } else {
      essential_nodes [ splitline[0] ] = false;
    }
  }
  // Index the node names
  uint64_t loop_index = 0;
  data_ -> essential_ . resize ( essential_nodes . size () );
  for ( auto const& name : data_ -> name_by_index_ ) { 
    data_ -> index_by_name_ [ name ] = loop_index; 
    data_ -> essential_ [ loop_index ] = essential_nodes [ name ];
    ++ loop_index;
  }
  // Learn the logics
  // Trick: ignore everything but node names and +'s. 
  // Example: a + ~ b c d + e  corresponds to (a+~b)(c)(d+e)
  uint64_t target = 0;
  for ( auto const& logic_string : logic_strings ) {
    //std::cout << "Processing " << logic_string << "\n";
    std::vector<std::vector<uint64_t>> logic_struct;
    std::vector<uint64_t> factor;
    std::string token;
    bool parity = true;
    bool appending = true;

    auto flush_factor = [&] () {
      if ( factor . empty () ) return;
      // Put factor into canonical ordering
      std::sort ( factor.begin(), factor.end() );
      logic_struct . push_back ( factor );
      //std::cout << "    Flushing factor ";
      //for ( uint64_t i : factor ) std::cout << name ( i ) << " ";
      //std::cout << "\n";
      factor . clear ();
    };

    auto flush_token = [&] () {
      if ( token . empty () ) return;
      if ( not appending ) flush_factor ();
      //std::cout << "  Flushing token " << token << "\n";
      
      auto splittoken = split ( token, '[' );
      //std::cout << "  Variable name: " << splittoken[0] << "\n";
      
      if ( data_ -> index_by_name_ . count ( splittoken[0] ) == 0 ) {
        throw std::runtime_error ( "Problem parsing network specification file: " 
                                   " Invalid input variable " + splittoken[0] );
      }
      uint64_t source = data_ -> index_by_name_ [ splittoken[0] ];
      factor . push_back ( source );
      if (splittoken.size() > 1) {
        //this means there was something inside brackets
        //std::cout << "  Threshold string: " << splittoken[1] << "\n";
        try {
          uint64_t threshold_count = std::stoi( splittoken[1] );
          for (uint64_t i = 0; i < threshold_count; i++) {
            data_ -> edge_type_[std::make_pair( source, target )] . push_back ( parity );
          }
        } catch ( const std::invalid_argument& e ) {
          for(char& c : splittoken[1]) {
            if (c == '+') {
              data_ -> edge_type_[std::make_pair( source, target )] . push_back ( parity );
            } else if (c == '-') {
              data_ -> edge_type_[std::make_pair( source, target )] . push_back ( !parity );
            }
          }
        }
      } else {
        data_ -> edge_type_[std::make_pair( source, target )] . push_back ( parity );
      }
      //std::cout << "Creating edge from " << source << " to " << target << "\n";
      token . clear ();
      appending = false;
      parity = true;
    };
    
    bool bracketed = false;
    
    for ( char c : logic_string ) {
      //std::cout << "Reading character " << c << "\n";
      if ( !bracketed ) {
        if ( c == '[' ) {
          bracketed = true;
        }
        if ( ( c == '\t' ) || (c == ' ') || (c == '(') || (c == ')') || (c == '+') || (c == '~') ) {
          flush_token ();
        } else {
          token . push_back ( c );
        }
        if ( c == '+' ) { 
          appending = true;
          //std::cout << "  Detected +\n";
        }
        if ( c == '~' ) parity = false;
      } else {
        if ( c == ']' ) {
          bracketed = false;
          flush_token ();
        } else {
          token . push_back ( c );
        }
      }
    }
    flush_token ();
    flush_factor ();
    //std::cout << "The logic_struct formed.\n";
    // Ensure logic_struct is acceptable (no repeats!)
    std::unordered_set<uint64_t> inputs;
    for ( auto const& factor : logic_struct ) {
      //std::cout << "# ";
      for ( auto i : factor ) {
        //std::cout << i << " ";
         if ( inputs . count ( i ) ) {
           throw std::runtime_error ( "Problem parsing network specification file: Repeated inputs in logic" );
         }
        inputs . insert ( i );
      }
    }
    //std::cout << "\n";
    //std::cout << "The logic_struct is acceptable.\n";
    // Compare partitions by (size, max), where size is length and max is maximum index
    auto compare_partition = [](std::vector<uint64_t> const& lhs, std::vector<uint64_t> const& rhs) {
      if ( lhs . size () < rhs . size () ) return true;
      if ( lhs . size () > rhs . size () ) return false;
      uint64_t max_lhs = * std::max_element ( lhs.begin(), lhs.end() );
      uint64_t max_rhs = * std::max_element ( rhs.begin(), rhs.end() );
      if ( max_lhs < max_rhs ) return true;
      if ( max_lhs > max_rhs ) return false;  /* unreachable -> */ return false;
    };
    // Put the logic struct into a canonical ordering.
    std::sort ( logic_struct.begin(), logic_struct.end(), compare_partition );
    data_ -> logic_by_index_ . push_back ( logic_struct );
    //std::cout << "The logic_struct has been incorporated into the network.\n";
    ++ target;
  }
  // Compute inputs and outputs.
  data_ -> inputs_ . resize ( size () );
  data_ -> outputs_ . resize ( size () );
//  data_ -> input_instances_ . resize ( size () );
  for ( target = 0; target < size (); ++ target ) {
    // Keep track of repeated inputs to target
    std::unordered_map<uint64_t, uint64_t> input_counts;
    for ( auto const& factor : logic ( target ) ) {
      for ( uint64_t source : factor ) {
//        uint64_t instance = 0; // Keep track of input instances
//        if ( input_counts . find (source) != input_counts . end() ) {
//          instance = input_counts . find (source) -> second;
//        }
//        input_counts [source] = instance + 1;
        data_ -> inputs_[target] . push_back ( source );
        data_ -> outputs_[source] . push_back ( target );
//        data_ -> input_instances_[target] . push_back ( instance );
        // Output order of this instance of edge (source, target)
//        data_ -> order_[std::make_tuple(source, target, instance)] = data_ -> outputs_[source].size() - 1;
        data_ -> order_[std::make_tuple(source, target)] = data_ -> outputs_[source].size() - 1;
      }
    }
  }
  // Generate a specification string for the helper network
  std::string helper_specification = "";
  for ( uint64_t target = 0; target < data_ -> name_by_index_.size(); target++ ) {
    helper_specification += data_ -> name_by_index_[target] + " : ";
    for ( auto const& factor : data_ -> logic_by_index_[target] ) {
      helper_specification += '(';
      bool plus = false;
      for ( auto source : factor ) {
        for ( auto sign : interaction( source, target ) ){
          if ( sign ) {
            if (plus) {
              helper_specification += " + " + data_ -> name_by_index_[source];
            } else {
              helper_specification += data_ -> name_by_index_[source];
              plus = true;
            }
          } else {
            if (plus) {
              helper_specification += " + ~" + data_ -> name_by_index_[source];
            } else {
              helper_specification += "~" + data_ -> name_by_index_[source];
              plus = true;
            }
          }
        }
      }
      helper_specification += ')';
    }
    if ( data_ -> essential_ [ target ] ) {
      helper_specification += " : E";
    }
    helper_specification += "\n";
  }
  //std::cout << helper_specification;
  data_ -> helper_network_ = Network(helper_specification);
  //std::cout << "_parse complete.\n";
}


//INLINE_IF_HEADER_ONLY std::ostream& operator << ( std::ostream& stream, MultipleThresholdNetwork const& network ) {
//  stream << "[";
//  bool first1 = true;
//  for ( uint64_t v = 0; v < network.size (); ++ v ) {
//    if ( first1 ) first1 = false; else stream << ",";
//    stream << "[\"" << network.name(v) << "\","; // node
//    std::vector<std::vector<uint64_t>> logic_struct = network.logic ( v );
//    stream << "["; // logic_struct
//    bool first2 = true;
//    for ( auto const& part : logic_struct ) {
//      if ( first2 ) first2 = false; else stream << ",";
//      stream << "["; // factor
//      bool first3 = true;
//      for ( uint64_t source : part ) {
//        if ( first3 ) first3 = false; else stream << ",";
//        std::string head = network.interaction(source,v) ? "" : "~";
//        stream << "\"" << head << network.name(source) << "\"";
//      }
//      stream << "]"; // factor
//    }
//    stream << "],"; // logic_struct
//    stream << "["; // outputs
//    bool first4 = true;
//    for ( uint64_t target : network.outputs ( v ) ) {
//      if ( first4 ) first4 = false; else stream << ",";
//      stream << "\"" << network.name(target) << "\"";
//    }
//    stream << "]"; // outputs 
//    stream << "]"; // node
//  }  
//  stream << "]"; // network
//  return stream;
//}
