/// Network.hpp
/// Shaun Harker
/// 2015-05-22
///
/// Marcio Gameiro
/// 2022-01-23

#pragma once

#ifndef INLINE_IF_HEADER_ONLY
#define INLINE_IF_HEADER_ONLY
#endif

#include "Network.h"

INLINE_IF_HEADER_ONLY Network::
Network ( void ) {
  data_ . reset ( new Network_ );
}

INLINE_IF_HEADER_ONLY Network::
Network ( std::string const& s ) {
  assign(s);
}

INLINE_IF_HEADER_ONLY void Network::
assign ( std::string const& s ) {
  auto colon = s.find(':');
  if ( colon != std::string::npos ) {
    data_ . reset ( new Network_ );
    data_ -> specification_ = s;
    _parse ( _lines () );
  } else {
    load(s);
  }
}

INLINE_IF_HEADER_ONLY void Network::
load ( std::string const& filename ) {
  data_ . reset ( new Network_ );
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

INLINE_IF_HEADER_ONLY uint64_t Network::
size ( void ) const {
  return data_ -> name_by_index_ . size ();
}

INLINE_IF_HEADER_ONLY uint64_t Network::
index ( std::string const& name ) const {
  return data_ -> index_by_name_ . find ( name ) -> second;
}

INLINE_IF_HEADER_ONLY std::string const& Network::
name ( uint64_t index ) const {
  return data_ -> name_by_index_[index];
}

INLINE_IF_HEADER_ONLY std::vector<uint64_t> const& Network::
inputs ( uint64_t index ) const {
  return data_ -> inputs_[index];
}

INLINE_IF_HEADER_ONLY std::vector<uint64_t> const& Network::
outputs ( uint64_t index ) const {
  return data_ -> outputs_[index];
}

INLINE_IF_HEADER_ONLY std::vector<uint64_t> const& Network:: 
input_instances ( uint64_t index ) const {
  return data_ -> input_instances_[index];
}

INLINE_IF_HEADER_ONLY std::vector<std::vector<uint64_t>> Network::
logic ( uint64_t index ) const {
  std::vector<std::vector<uint64_t>> logic_struct;
  for ( auto const& factor : logic_by_index ( index ) ) {
    std::vector<uint64_t> logic_factor;
    for ( auto edge : factor ) {
      uint64_t source = std::get<0>(edge);
      // uint64_t instance = std::get<1>(edge);
      logic_factor . push_back ( source );
    }
    logic_struct . push_back ( logic_factor );
  }
  return logic_struct;
}

INLINE_IF_HEADER_ONLY std::vector<std::vector<std::pair<uint64_t,uint64_t>>> const& Network::
logic_by_index ( uint64_t index ) const {
  return data_ -> logic_by_index_ [ index ];
}

INLINE_IF_HEADER_ONLY bool Network::
essential ( uint64_t index ) const {
  return data_ -> essential_ [ index ];
}

INLINE_IF_HEADER_ONLY bool Network::
interaction ( uint64_t source, uint64_t target, uint64_t instance ) const {
  return data_ -> edge_type_ . find ( std::make_tuple ( source, target, instance ) ) -> second;
}

INLINE_IF_HEADER_ONLY bool Network::
ptm ( uint64_t source, uint64_t target, uint64_t instance ) const {
  return data_ -> ptm_edge_ . find ( std::make_tuple ( source, target, instance ) ) -> second;
}

INLINE_IF_HEADER_ONLY bool Network::
decay ( uint64_t source, uint64_t target, uint64_t instance ) const {
  return data_ -> decay_edge_ . find ( std::make_tuple ( source, target, instance ) ) -> second;
}

INLINE_IF_HEADER_ONLY uint64_t Network::
num_thresholds ( uint64_t index ) const {
  return data_ -> num_thresholds_ [ index ];
}

INLINE_IF_HEADER_ONLY uint64_t Network::
order ( uint64_t source, uint64_t target, uint64_t instance ) const {
  return data_ ->  order_ . find ( std::make_tuple (source, target, instance) ) -> second;
}

INLINE_IF_HEADER_ONLY std::vector<uint64_t> Network::
domains ( void ) const {
  std::vector<uint64_t> result;
  for ( auto n_thresholds : data_ -> num_thresholds_ ) {
    result . push_back ( n_thresholds + 1 );
  }
  return result;
}

INLINE_IF_HEADER_ONLY std::string Network::
specification ( void ) const {
  return data_ -> specification_;
}

INLINE_IF_HEADER_ONLY std::string Network::
graphviz ( std::string const& join_type, std::vector<std::string> const& theme ) const {
  // PTM edges are joined according to the value of join_type. The options
  // are "p" (for point), "c" (for circle), and "s" (for square). The
  // default value for join_type is "", which uses the default type "p"
  std::string join_node = join_type.empty() ? "p" : join_type;
  if ( not ( join_node == "p" or join_node == "c" or join_node == "s" ) ) {
    throw std::runtime_error ( "Invalid join node type " + join_type );
  }
  std::stringstream result;
  std::stringstream edges;
  // std::cout << "graphviz. Looping through nodes.\n";
  result << "digraph {\n";
  result << "bgcolor = " << theme[0] << "; nodesep = 0.35;\n";
  for ( uint64_t i = 0; i < size (); ++ i ) {
    result << "\"" << name(i) << "\"" << " [style=filled, fillcolor=" << theme[1] << "];\n";
  }
  std::string normalhead ("normal");
  std::string blunthead ("tee");
  std::string dashed ("dashed");
  std::string solid ("solid");
  uint64_t num_ptm_pairs = 0;
  // std::cout << "graphviz. Looping through edges.\n";
  for ( uint64_t target = 0; target < size (); ++ target ) {
    std::vector<std::vector<std::pair<uint64_t,uint64_t>>> logic_struct = logic_by_index ( target );
    std::reverse ( logic_struct . begin (), logic_struct . end () ); // prefer black
    uint64_t partnum = 0;
    for ( auto const& factor : logic_struct ) {
      bool first = true;
      uint64_t new_node1;
      uint64_t new_node2;
      uint64_t new_node3;
      uint64_t ptm_source1;
      uint64_t ptm_source2;
      for ( auto edge : factor ) {
        uint64_t source = std::get<0>(edge);
        uint64_t instance = std::get<1>(edge);
        // std::cout << "Checking type of edge from " << source << " to " << target << "\n";
        if ( ptm (source, target, instance) ) {
          if ( first ) { // PTM pair found
            ptm_source1 = source; // First node of PTM pair
            // Add additional node(s) to join pair
            if ( join_node == "p" ) { // Add 3 extra nodes
              new_node1 = size () + 3 * num_ptm_pairs;
              new_node2 = new_node1 + 1;
              new_node3 = new_node1 + 2;
              // Add invisible points as the extra nodes
              result << "\"" << new_node1 << "\"" << " [shape=point, label=none, height=0, width=0]" << ";\n";
              result << "\"" << new_node2 << "\"" << " [shape=point, label=none, height=0, width=0]" << ";\n";
              result << "\"" << new_node3 << "\"" << " [shape=point, label=none, height=0, width=0]" << ";\n";
            }
            else { // Add 1 extra node
              new_node1 = size () + num_ptm_pairs;
              // Get shape of the extra node
              std::string shape = join_node == "c" ? "circle" : "square";
              result << "\"" << new_node1 << "\"" << " [shape=" << shape << ", label=\"\", width=0.15]" << ";\n";
            }
            num_ptm_pairs++;
            first = false;
          }
          else {
            ptm_source2 = source; // Second node of PTM pair
            std::string line_style = decay (ptm_source1, target, instance) ? dashed : solid;
            if ( join_node == "p" ) { // Add 3 extra edges
              // Add edge from source1 to intermediate node 1
              std::string head1 = interaction (ptm_source1, target, instance) ? normalhead : blunthead;
              edges << "\"" << name(ptm_source1) << "\" -> \"" << new_node1 << "\" [color=" << theme[partnum + 2]
                    << ", style=" << line_style << ", arrowhead=" << head1 << ", weight=0, headport=n];\n";
              // Add edge from intermediate node 1 to intermediate node 3
              edges << "\"" << new_node1 << "\" -> \"" << new_node3 << "\" [color=" << theme[partnum + 2]
                    << ", style=" << line_style << ", dir=none, weight=0, tailport=s, headport=n];\n";
              // Add edge from source2 to intermediate node 2
              std::string head2 = interaction (ptm_source2, target, instance) ? normalhead : blunthead;
              edges << "\"" << name(ptm_source2) << "\" -> \"" << new_node2 << "\" [color=" << theme[partnum + 2]
                    << ", style=" << line_style << ", arrowhead=" << head2 << ", weight=0, headport=n];\n";
              // Add edge from intermediate node 2 to intermediate node 3
              edges << "\"" << new_node2 << "\" -> \"" << new_node3 << "\" [color=" << theme[partnum + 2]
                    << ", style=" << line_style << ", dir=none, weight=0, tailport=s, headport=n];\n";
              // Do not use self edges in the ranking the the nodes
              std::string constraint = ( (ptm_source1 == target) or (ptm_source2 == target) ) ? "false" : "true";
              // Add edge from intermediate node 3 to target
              edges << "\"" << new_node3 << "\" -> \"" << name(target) << "\" [color=" << theme[partnum + 2]
                    << ", style=" << line_style << ", dir=none, weight=0, constraint=" << constraint << ", tailport=s];\n";
            }
            else { // Add 1 extra edge
              // Add edge from source1 to the intermediate node
              std::string head1 = interaction (ptm_source1, target, instance) ? normalhead : blunthead;
              edges << "\"" << name(ptm_source1) << "\" -> \"" << new_node1 << "\" [color=" << theme[partnum + 2]
                    << ", style=" << line_style << ", arrowhead=" << head1 << "];\n";
              // Add edge from source2 to the intermediate node
              std::string head2 = interaction (ptm_source2, target, instance) ? normalhead : blunthead;
              edges << "\"" << name(ptm_source2) << "\" -> \"" << new_node1 << "\" [color=" << theme[partnum + 2]
                    << ", style=" << line_style << ", arrowhead=" << head2 << "];\n";
              // Do not use self edges in ranking the nodes
              std::string constraint = ( (ptm_source1 == target) or (ptm_source2 == target) ) ? "false" : "true";
              // Add edge from intermediate node to target
              edges << "\"" << new_node1 << "\" -> \"" << name(target) << "\" [color=" << theme[partnum + 2]
                    << ", style=" << line_style << ", dir=none, constraint=" << constraint << "];\n";
            }
            first = true;
          }
        }
        else {
          std::string head = interaction (source, target, instance) ? normalhead : blunthead;
          std::string line_style = decay (source, target, instance) ? dashed : solid;
          edges << "\"" << name(source) << "\" -> \"" << name(target) << "\" [color=" << theme[partnum + 2]
                << ", style=" << line_style << ", arrowhead=" << head << "];\n";
        }
      }
      ++ partnum;
      if ( partnum + 2 == theme . size () ) partnum = 0;
    }
  }
  result << edges . str() << "}\n";
  return result . str ();
}

namespace DSGRN_parse_tools {
  // http://stackoverflow.com/questions/236129/split-a-string-in-c
  INLINE_IF_HEADER_ONLY std::vector<std::string> &split(const std::string &s, char delim, std::vector<std::string> &elems) {
    std::stringstream ss(s);
    std::string item;
    while (std::getline(ss, item, delim)) {
        elems.push_back(item);
    }
    return elems;
  }
  INLINE_IF_HEADER_ONLY std::vector<std::string> split(const std::string &s, char delim) {
    std::vector<std::string> elems;
    split(s, delim, elems);
    return elems;
  }
  INLINE_IF_HEADER_ONLY std::string& removeSpace ( std::string &s ) {
    s.erase(std::remove_if(s.begin(), s.end(), (uint64_t(*)(uint64_t))isspace), s.end());
    return s;
  }
}

/// _lines
///   Open the network file and read it line by line
INLINE_IF_HEADER_ONLY std::vector<std::string> Network::
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
INLINE_IF_HEADER_ONLY void Network::
_parse ( std::vector<std::string> const& lines ) {
  using namespace DSGRN_parse_tools;
  // Edge type to locally store edge information
  // (source, parity, ptm_edge, decay_edge)
  typedef std::tuple<uint64_t,bool,bool,bool> EdgeTuple;
  std::vector<std::string> logic_strings;
  std::map<std::string, bool> essential_nodes;
  // std::vector<std::string> constraint_strings;
  // Learn the node names
  for ( auto const& line : lines ) {
    auto splitline = split ( line, ':' );
    if ( splitline . empty () ) continue;
    removeSpace(splitline[0]);
    // Skip if empty string
    if ( splitline[0] == "" ) continue;
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
  for ( auto const& name : data_ ->  name_by_index_ ) {
    data_ -> index_by_name_ [ name ] = loop_index;
    data_ -> essential_ [ loop_index ] = essential_nodes [ name ];
    ++ loop_index;
  }
  // Learn the logics
  // Trick: ignore everything but node names and +'s.
  // Example: a + ~ b c d + e  corresponds to (a+~b)(c)(d+e)
  // PTM decay edges are inside <>
  // PTM non-decay pairs are inside []
  // Example: < a + b > + [c, d] e
  uint64_t target = 0;
  for ( auto const& logic_string : logic_strings ) {
    // std::cout << "Processing " << logic_string << "\n";
    // Final input logic structure to a node: (source, instance)
    std::vector<std::vector<std::pair<uint64_t,uint64_t>>> logic_by_index;
    // Intermediate (temporary) logic structure
    std::vector<std::vector<EdgeTuple>> logic_struct;
    std::vector<EdgeTuple> factor;
    std::string token;
    uint64_t ptm_term_size = 0;   // Size of PTM term
    uint64_t commas_found = 0;    // Number of commas in PTM term
    bool decay_term = false;      // True if there is a decay term
    bool ptm_term = false;        // True if there is a ptm term
    bool first_char = false;      // True if first char was processed
    bool last_decay_char = false; // True if last char is last decay char
    bool ptm_factor = false;      // True if current factor has PTM edges
    bool decay_edge = false;
    bool ptm_edge = false;
    bool parity = true;
    bool appending = true;

    auto sort_factor = [&] () {
      std::vector<std::vector<EdgeTuple>> ptm_pairs;
      std::vector<EdgeTuple> regular_edges;
      uint64_t k = 0;
      while ( k < factor . size() ) {
        EdgeTuple edge1 = factor [k];
        // Check if it is a PTM edge
        bool ptm_flag = std::get<2>(edge1);
        if ( ptm_flag ) {
          EdgeTuple edge2 = factor [k + 1];
          std::vector<EdgeTuple> pair = { edge1, edge2 };
          // Do not sort edges in a PTM pair
          ptm_pairs . push_back ( pair );
          k += 2;
        }
        else {
          regular_edges . push_back ( edge1 );
          k++;
        }
      }
      // Sort PTM pairs by source (first entry) of first element
      auto cmp_pairs = [](auto const& lhs, auto const& rhs) {
        return std::get<0>(lhs [0]) < std::get<0>(rhs [0]);
      };
      std::sort ( ptm_pairs . begin(), ptm_pairs . end(), cmp_pairs );
      // Sort edge tuples by source (first entry)
      auto cmp_edges = [](auto const& e1, auto const& e2) {
        return std::get<0>(e1) < std::get<0>(e2);
      };
      std::sort ( regular_edges . begin(), regular_edges . end(), cmp_edges );
      factor . clear ();
      // Put PTM edges before regular edges
      for ( auto pair : ptm_pairs ) {
        factor . push_back ( pair[0] );
        factor . push_back ( pair[1] );
      }
      for ( auto edge : regular_edges ) {
        factor . push_back ( edge );
      }
    };

    auto flush_factor = [&] () {
      if ( factor . empty () ) return;
      // Put factor into canonical ordering
      sort_factor ();
      logic_struct . push_back ( factor );
      // std::cout << "    Flushing factor ";
      // for ( uint64_t i : factor ) std::cout << name ( i ) << " ";
      // std::cout << "\n";
      factor . clear ();
      ptm_factor = false;
    };

    auto flush_token = [&] () {
      if ( token . empty () ) return;
      if ( not appending ) flush_factor ();
      // std::cout << "  Flushing token " << token << "\n";
      if ( data_ -> index_by_name_ . count ( token ) == 0 ) {
        throw std::runtime_error ( "Problem parsing network specification file: "
                                   " Invalid input variable " + token );
      }
      uint64_t source = data_ -> index_by_name_ [ token ];
      factor . push_back ( std::make_tuple(source, parity, ptm_edge, decay_edge) );
      // factor . push_back ( source );
      // data_ -> edge_type_ [std::make_pair( source, target )] = parity;
      // data_ -> ptm_edge_ [std::make_pair( source, target )] = ptm_edge;
      // data_ -> decay_edge_ [std::make_pair( source, target )] = decay_edge;
      // std::cout << "Creating edge from " << source << " to " << target << "\n";
      token . clear ();
      if ( ptm_edge ) ptm_term_size++;
      appending = false;
      parity = true;
    };

    for ( char c : logic_string ) {
      // std::cout << "Reading character " << c << "\n";
      if ( ( c == '\t' ) || ( c == ' ' ) || ( c == '(' ) || ( c == ')' ) ||
           ( c == '+' ) || ( c == '~' ) || ( c == ',' ) || ( c == '[' ) ||
           ( c == ']' ) || ( c == '<' ) || ( c == '>' ) ) {
        flush_token ();
      } else {
        token . push_back ( c );
      }
      if ( c == '+' ) appending = true;
      if ( c == '~' ) parity = false;
      // The char after the last decay term char must be +
      if ( last_decay_char and ( c != '\t' ) and ( c != ' ' ) ) {
        if ( c != '+' ) {
          throw std::runtime_error ( "Problem parsing network specification: Missing + after decay term" );
        }
        appending = false; // This + does not count for the logic
        last_decay_char = false;
      }
      if ( c == ',' ) {
        if ( ptm_term_size != 1 ) {
          throw std::runtime_error ( "Problem parsing network specification: Invalid , detected" );
        }
        commas_found++;
        appending = true; // Make PTM edges part of the same factor
      }
      if ( ( c == ',' ) and ( not ptm_edge ) ) {
        throw std::runtime_error ( "Problem parsing network specification: Invalid , detected" );
      }
      if ( c == '<' ) {
        if ( first_char ) { // If first char was already processed
          throw std::runtime_error ( "Problem parsing network specification: Decay term must be at the beginning" );
        }
        if ( decay_term ) {
          throw std::runtime_error ( "Problem parsing network specification: Double < detected" );
        }
        decay_edge = true;
        decay_term = true;
      }
      if ( c == '>' ) {
        if ( not decay_edge ) {
          throw std::runtime_error ( "Problem parsing network specification: No opening <" );
        }
        decay_edge = false;
        last_decay_char = true;
      }
      if ( c == '[' ) {
        if ( ptm_edge ) {
          throw std::runtime_error ( "Problem parsing network specification: Double [ detected" );
        }
        ptm_edge = true;
        ptm_factor = true;
        ptm_term = true;
      }
      if ( c == ']' ) {
        if ( not ptm_edge ) {
          throw std::runtime_error ( "Problem parsing network specification: No opening [" );
        }
        // PTM terms must have size 2
        if ( ptm_term_size != 2 ) {
          throw std::runtime_error ( "Problem parsing network specification: PTM terms size must be 2" );
        }
        // Must have exactly 1 comma
        if ( commas_found != 1 ) {
          throw std::runtime_error ( "Problem parsing network specification: Invalid , detected" );
        }
        ptm_term_size = 0;
        commas_found = 0;
        ptm_edge = false;
      }
      if ( ( c != '\t' ) and ( c != ' ' ) ) {
        first_char = true; // First char processed
      }
    }
    // Done processing logic_string
    // Check if < and all [ were closed
    if ( decay_edge ) {
      throw std::runtime_error ( "Problem parsing network specification: No closing >" );
    }
    if ( ptm_edge ) {
      throw std::runtime_error ( "Problem parsing network specification: No closing ]" );
    }
    flush_token ();
    flush_factor ();
    // std::cout << "The logic_struct formed.\n";

    // Check if factor is a decay factor
    auto decayfactor = [&](auto const& factor) {
      for ( auto edge : factor ) {
        bool decay_flag = std::get<3>(edge);
        if ( decay_flag )
          return true;
      }
      return false;
    };

    // // Check if factor is a ptm factor
    // auto ptmfactor = [&](auto const& factor) {
    //   for ( auto edge : factor ) {
    //     bool ptm_flag = std::get<2>(edge);
    //     if ( ptm_flag )
    //       return true;
    //   }
    //   return false;
    // };

    // Get number of ptm edges in factor
    auto num_ptm_edges = [&](auto const& factor) {
      uint64_t num_ptmedges = 0;
      for ( auto edge : factor ) {
        bool ptm_flag = std::get<2>(edge);
        if ( ptm_flag )
          num_ptmedges += 1;
      }
      return num_ptmedges;
    };

    // Compare factors by (total order size, reverse ptm size, max),
    // where total order size is the number of ptm pairs plus the number
    // of regular edges, ptm size is the number of ptm pairs, and max is
    // maximum index, but put decay factors before non-decay factors
    auto cmp_factors = [&](auto const& lhs, auto const& rhs) {
      // Put decay factors first
      if ( decayfactor ( lhs ) and not decayfactor ( rhs ) )
        return true;
      if ( decayfactor ( rhs ) and not decayfactor ( lhs ) )
        return false;
      // Compare the remaining factors by (total order size, reverse
      // ptm size, max), where total order size is the number of ptm
      // pairs plus the number of regular edges, ptm size is the number
      // of ptm pairs, and max is maximum index.
      // Compare factors by number of ptm pairs plus regular edges
      uint64_t n_ptm_edges_lhs = num_ptm_edges (lhs);
      uint64_t n_ptm_edges_rhs = num_ptm_edges (rhs);
      // Size of total order factor (num ptm pairs plus num regular edges)
      uint64_t size_lhs = (n_ptm_edges_lhs / 2) + (lhs . size () - n_ptm_edges_lhs);
      uint64_t size_rhs = (n_ptm_edges_rhs / 2) + (rhs . size () - n_ptm_edges_rhs);
      if ( size_lhs < size_rhs )
        return true;
      if ( size_rhs < size_lhs )
        return false;
      // Compare factors by reverse ptm sizes
      if ( n_ptm_edges_lhs < n_ptm_edges_rhs )
        return false;
      if ( n_ptm_edges_rhs < n_ptm_edges_lhs )
        return true;
      // Compare edge tuples by source (first entry)
      auto cmp_edges = [](auto const& e1, auto const& e2) {
        return std::get<0>(e1) < std::get<0>(e2);
      };
      auto edge_max_lhs = * std::max_element ( lhs.begin(), lhs.end(), cmp_edges );
      auto edge_max_rhs = * std::max_element ( rhs.begin(), rhs.end(), cmp_edges );
      uint64_t max_lhs = std::get<0>(edge_max_lhs);
      uint64_t max_rhs = std::get<0>(edge_max_rhs);
      if ( max_lhs < max_rhs ) return true;
      if ( max_lhs > max_rhs ) return false;
      // Return false if everything is the same
      return false;
    };

    // Put the logic struct into a canonical ordering
    std::sort ( logic_struct.begin(), logic_struct.end(), cmp_factors );
    // Transform the logic structure to its final format: (source, instance)
    // Keep track of repeated inputs to target
    std::unordered_map<uint64_t, uint64_t> input_counts;
    for ( auto const& logic_factor : logic_struct ) {
        // Represent input edges by a pair (source, instance)
        std::vector<std::pair<uint64_t,uint64_t>> factor;
        for ( auto edge : logic_factor ) {
          uint64_t source = std::get<0>(edge);
          bool parity = std::get<1>(edge);
          bool ptm_edge = std::get<2>(edge);
          bool decay_edge = std::get<3>(edge);
          uint64_t instance = 0; // Keep track of input instances
          if ( input_counts . find (source) != input_counts . end() ) {
            instance = input_counts . find (source) -> second;
          }
          input_counts [source] = instance + 1;
          // Add edge (source, instance) to factor
          factor . emplace_back ( source, instance );
          // Keep track of parity, PTM edges, and decay edges
          data_ -> edge_type_ [std::make_tuple( source, target, instance )] = parity;
          data_ -> ptm_edge_ [std::make_tuple( source, target, instance )] = ptm_edge;
          data_ -> decay_edge_ [std::make_tuple( source, target, instance )] = decay_edge;
        }
        // Add factor to logic structure
        logic_by_index . push_back ( factor );
    }

    // Incorporated sorted logic structure into the network
    data_ -> logic_by_index_ . push_back ( logic_by_index );
    // std::cout << "The logic_struct has been incorporated into the network.\n";
    ++ target;
  } // for ( auto const& logic_string : logic_strings )

  // Compute inputs and outputs
  data_ -> inputs_ . resize ( size () );
  data_ -> outputs_ . resize ( size () );
  data_ -> input_instances_ . resize ( size () );
  for ( uint64_t target = 0; target < size (); ++ target ) {
    for ( auto const& factor : logic_by_index ( target ) ) {
      for ( auto edge : factor ) {
        uint64_t source = std::get<0>(edge);
        uint64_t instance = std::get<1>(edge);
        data_ -> inputs_ [target] . push_back ( source );
        data_ -> outputs_ [source] . push_back ( target );
        data_ -> input_instances_ [target] . push_back ( instance );
        // Output order of this instance of edge (source, target)
        data_ -> order_[std::make_tuple(source, target, instance)] = data_ -> outputs_[source].size() - 1;
      }
    }
  }

  // Set number of thresholds for each node
  data_ -> num_thresholds_ . resize ( size () );
  for ( uint64_t d = 0; d < size (); ++ d ) {
    std::vector<uint64_t> outedges = outputs ( d );
    // Treat the no out edge case as one out edge
    uint64_t m = outedges . size() ? outedges . size() : 1;
    // Get the number of self edges
    uint64_t n_self_edges = std::count( outedges . begin(), outedges . end(), d );
    // Each self edge creates an additional threshold
    data_ -> num_thresholds_[d] = m + n_self_edges;
  }
  // std::cout << "_parse complete.\n";
}

INLINE_IF_HEADER_ONLY std::ostream& operator << ( std::ostream& stream, Network const& network ) {
  stream << "[";
  bool first1 = true;
  for ( uint64_t v = 0; v < network . size (); ++ v ) {
    if ( first1 ) first1 = false; else stream << ",";
    stream << "[\"" << network . name(v) << "\","; // node
    auto logic_struct = network . logic_by_index ( v );
    stream << "["; // logic_struct
    bool first2 = true;
    for ( auto const& factor : logic_struct ) {
      if ( first2 ) first2 = false; else stream << ",";
      stream << "["; // factor
      bool first3 = true;
      for ( auto edge : factor ) {
        if ( first3 ) first3 = false; else stream << ",";
        uint64_t source = std::get<0>(edge);
        uint64_t instance = std::get<1>(edge);
        std::string head = network . interaction(source, v, instance) ? "" : "~";
        stream << "\"" << head << network . name(source) << "\"";
      }
      stream << "]"; // factor
    }
    stream << "],"; // logic_struct
    stream << "["; // outputs
    bool first4 = true;
    for ( uint64_t target : network . outputs ( v ) ) {
      if ( first4 ) first4 = false; else stream << ",";
      stream << "\"" << network . name(target) << "\"";
    }
    stream << "]"; // outputs
    stream << "]"; // node
  }  
  stream << "]"; // network
  return stream;
}
