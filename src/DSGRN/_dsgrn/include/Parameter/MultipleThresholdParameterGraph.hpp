/// MultipleThresholdParameterGraph.hpp
/// Shaun Harker
/// 2015-05-24
/// Marcio Gameiro
/// 2020-10-06
/// Adam Zheleznyak
/// 2021-01-18

#pragma once

#ifndef INLINE_IF_HEADER_ONLY
#define INLINE_IF_HEADER_ONLY
#endif

#include "MultipleThresholdParameterGraph.h"

INLINE_IF_HEADER_ONLY MultipleThresholdParameterGraph::
MultipleThresholdParameterGraph ( void ) {
  data_ . reset ( new MultipleThresholdParameterGraph_ );
}

INLINE_IF_HEADER_ONLY MultipleThresholdParameterGraph::
MultipleThresholdParameterGraph ( MultipleThresholdNetwork const& network ) {
  assign ( network );
}

INLINE_IF_HEADER_ONLY void MultipleThresholdParameterGraph::
assign ( MultipleThresholdNetwork const& network ) {
  typedef bool bitType;
  typedef std::vector<bitType> BitContainer;
  // Convert an hex char into a vector of bits (length 4)
  // standard order (right to left)
  static std::unordered_map<char, BitContainer> hex_lookup =
  { { '0', {0,0,0,0} }, { '1', {0,0,0,1} }, { '2', {0,0,1,0} },
    { '3', {0,0,1,1} }, { '4', {0,1,0,0} }, { '5', {0,1,0,1} },
    { '6', {0,1,1,0} }, { '7', {0,1,1,1} }, { '8', {1,0,0,0} },
    { '9', {1,0,0,1} }, { 'A', {1,0,1,0} }, { 'B', {1,0,1,1} },
    { 'C', {1,1,0,0} }, { 'D', {1,1,0,1} }, { 'E', {1,1,1,0} },
    { 'F', {1,1,1,1} }
  };
  auto Hex2Bin = [&](char c) {
    return hex_lookup[c];
  };
  //
  // convert a string of hex code into vector of bits.
  auto Hex2BinCode = [&Hex2Bin] ( const std::string & str ) -> BitContainer {
    BitContainer output;
    for ( const char & c : str ) {
      // Need to reverse the order
      BitContainer nybble = Hex2Bin ( c );
      for ( bool b : nybble ) output . push_back ( b );
    }
    return output;
  };
  //
  static const std::vector<char> hex_digit =
  {'0','1','2','3','4','5','6','7','8','9','A','B','C','D','E','F'};
  auto Bin2HexCode = [&] ( const BitContainer & bin ) -> std::string {
    std::string result;
    for ( uint64_t i = 0; i < bin . size (); i += 4 ) {
      short digit = ( (short) bin[i] << 3 ) + ( (short) bin[i+1] << 2 )
      + ( (short) bin[i+2] << 1 ) + ( (short) bin [i+3] );
      result . push_back ( hex_digit [ digit ] );
    }
    return result;
  };
  
  
  std::string path = configuration() -> get_path() + "/logic";
  data_ . reset ( new MultipleThresholdParameterGraph_ );
  data_ -> network_ = network;
  data_ -> reorderings_ = 1;
  data_ -> fixedordersize_ = 1;
  // Load the logic files one by one.
  uint64_t D = data_ -> network_ . size ();
  for ( uint64_t d = 0; d < D; ++ d ) {
    uint64_t n = data_ -> network_ . helper_network() . inputs ( d ) . size ();
    uint64_t m = data_ -> network_ . helper_network() . outputs ( d ) . size ();
//    uint64_t order_count = _factorial ( m );
//    for ( auto const& output : data_ ->  network_ . outputs ( d ) ) {
//      if ( data_ -> network_ . threshold_count( d, output ) > 1 ) {
//        order_count /= _factorial ( data_ -> network_ . threshold_count( d, output ) );
//      }
//    }
    
    //Suboptimal but filter through all parameters based on index and ignore the ones where the order is unachievable
    
    std::vector<uint64_t> good_order_indices;
    std::unordered_map<std::uint64_t,uint64_t> good_order_indices_inverse;
    std::vector<uint64_t> first_threshold_index;
    uint64_t count = 0;
    
    for ( auto const& output : data_ ->  network_ . outputs ( d ) ) {
      first_threshold_index . push_back ( count );
      count += data_ -> network_ . threshold_count( d, output );
    }
    
    count = 0;
    for ( uint64_t order_index = 0; order_index < _factorial( m ); order_index++ ) {
      std::vector<uint64_t> tail_rep = _index_to_tail_rep ( order_index );
      tail_rep . resize ( m );
      std::vector<uint64_t> permute = _tail_rep_to_perm ( tail_rep );
      
      // this vector contains which out edges can be next so that edges corresponding to multiple thresholds are in the correct order
      bool good_order = true;
      std::vector<uint64_t>::iterator it;
      std::vector<uint64_t> next_thresholds = first_threshold_index;
      for (auto const& i : permute) {
        it = std::find(next_thresholds.begin(), next_thresholds.end(), i);
        if ( it != next_thresholds.end() ) {
          next_thresholds[std::distance(next_thresholds.begin(), it)] += 1;
        } else {
          good_order = false;
          break;
        }
      }
      if ( good_order ) {
        good_order_indices . push_back ( order_index );
        good_order_indices_inverse [ order_index ] = count;
        count++;
      }
    }
    data_ -> order_index_to_helper_ . push_back ( good_order_indices );
    data_ -> helper_to_order_index_ . push_back ( good_order_indices_inverse );
    data_ -> order_place_bases_ . push_back ( good_order_indices . size() );
    data_ -> reorderings_ *= data_ -> order_place_bases_ . back ();
    
    std::vector<std::vector<uint64_t>> const& logic_struct = data_ -> network_ . helper_network() . logic ( d );
    std::stringstream ss;
    ss << path << "/" << n <<  "_" << m;
    for ( auto const& p : logic_struct ) ss <<  "_" << p.size();
    if ( data_ -> network_ . helper_network() . essential ( d ) ) ss << "_E";
    ss << ".dat";
    //std::cout << "Acquiring logic data in " << ss.str() << "\n";
    std::vector<std::string> hex_codes;
    std::ifstream infile ( ss.str() );
    if ( not infile . good () ) {
      throw std::runtime_error ( "Error: Could not find logic resource " + ss.str() + ".\n");
    }
    
    bool multiple_thresholds_in = false;
    std::vector<bool> bits_to_keep_unexpanded ( pow( 2, n ), true );
    std::vector<bool> bits_to_keep;
    count = 0;
    
    std::vector<uint64_t> handled_inputs; //as we have unique inputs
    
    for ( auto const& factor : data_ -> network_ . helper_network() . logic ( d ) ) {
      for ( auto const& input : factor ) {
        if ( std::find(handled_inputs.begin(), handled_inputs.end(), input ) == handled_inputs.end() ) {
          uint64_t threshold_count = data_ -> network_ . threshold_count( input, d );
          if ( threshold_count > 1 ) {
            multiple_thresholds_in = true;
          }
          std::vector<uint64_t> good_bits;
          for ( uint64_t i = 0; i <= threshold_count; i++ ) {
            good_bits . push_back ( pow( 2, i ) - 1 );
          }
          for ( uint64_t bit = 0; bit < pow( 2, threshold_count ); bit++ ) {
            if ( std::find(good_bits.begin(), good_bits.end(), bit ) == good_bits.end() ) {
              for ( uint64_t j = 0; j < pow ( 2, n - count - threshold_count ) ; j++ ) {
                for ( uint64_t k = 0; k < pow( 2, count ); k++ ) {
                  bits_to_keep_unexpanded[ j * pow( 2, count + threshold_count ) + pow( 2, count ) * bit + k ] = false;
                }
              }
            }
          }
//          for ( auto const& bit : bits_to_keep_unexpanded ) {
//            std::cout << int(bit);
//          }
//          std::cout << "\n";
          handled_inputs . push_back ( input );
          count += threshold_count;
        }
      }
    }
    
    reverse( bits_to_keep_unexpanded.begin(), bits_to_keep_unexpanded.end() );
    
    for ( auto const& bit : bits_to_keep_unexpanded ) {
      for ( uint64_t i = 0; i < m; i++ ) {
        bits_to_keep . push_back ( bit );
      }
    }
    
    std::string line;
    std::unordered_map<std::string,uint64_t> hx;
    uint64_t counter = 0;
    if (multiple_thresholds_in) {
      while ( std::getline ( infile, line ) ) {
        // ignore bits that describe unachievable phase regions
        BitContainer binCode ( Hex2BinCode ( line ) );
        
        for ( uint64_t i = 0; i < m * pow( 2 , n ); i++ ) {
          binCode[i] = bits_to_keep[i] && binCode[i];
        }
        
        std::string code = Bin2HexCode ( binCode );
        
        if ( std::find(hex_codes.begin(), hex_codes.end(), code) == hex_codes.end() ) {
          hex_codes . push_back ( code );
          hx [ code ] = counter;
          ++counter;
        }
      }
    } else {
      while ( std::getline ( infile, line ) ) {
        hex_codes . push_back ( line );
        hx [ line ] = counter;
        ++counter;
      }
    }
    infile . close ();
    data_ -> factors_ . push_back ( hex_codes );
    data_ -> factors_inv_ . push_back ( hx );
    data_ -> logic_place_bases_ . push_back ( hex_codes . size () );
    data_ -> fixedordersize_ *= hex_codes . size ();
    //std::cout << d << ": " << hex_codes . size () << " factorial(" << m << ")=" << _factorial ( m ) << "\n";
  }
  data_ -> size_ = data_ -> fixedordersize_ * data_ -> reorderings_;
  // construction of place_values_ used in method index
  data_ -> logic_place_values_ . resize ( D, 0 );
  data_ -> order_place_values_ . resize ( D, 0 );
  data_ -> logic_place_values_ [ 0 ] = 1;
  data_ -> order_place_values_ [ 0 ] = 1;
  for ( uint64_t i = 1; i < D; ++ i ) {
    data_ -> logic_place_values_ [ i ] = data_ -> logic_place_bases_ [ i - 1 ] *
                                   data_ -> logic_place_values_ [ i - 1 ];
    data_ -> order_place_values_ [ i ] = data_ -> order_place_bases_ [ i - 1 ] *
                                  data_ -> order_place_values_ [ i - 1 ];
  }
}

INLINE_IF_HEADER_ONLY uint64_t MultipleThresholdParameterGraph::
size ( void ) const {
  return data_ -> size_;
}

INLINE_IF_HEADER_ONLY uint64_t MultipleThresholdParameterGraph::
dimension ( void ) const {
  return network().size();
}

INLINE_IF_HEADER_ONLY uint64_t MultipleThresholdParameterGraph::
logicsize ( uint64_t i ) const {
  return data_ -> logic_place_bases_ [ i ];
}

INLINE_IF_HEADER_ONLY uint64_t MultipleThresholdParameterGraph::
ordersize ( uint64_t i ) const {
  return data_ -> order_place_bases_ [ i ];
}

INLINE_IF_HEADER_ONLY std::vector<std::string> const& MultipleThresholdParameterGraph::
factorgraph ( uint64_t i ) const {
  return data_ -> factors_[i];
}

INLINE_IF_HEADER_ONLY Parameter MultipleThresholdParameterGraph::
parameter ( uint64_t index ) const {
  //std::cout << data_ -> "ParameterGraph::parameter( " << index << " )\n";
  if ( index >= size () ) {
    throw std::runtime_error ( "MultipleThresholdParameterGraph::parameter Index out of bounds");
  }
  uint64_t logic_index = index % data_ -> fixedordersize_;
  uint64_t order_index = index / data_ -> fixedordersize_;

  uint64_t D = data_ -> network_ . size ();
  std::vector<uint64_t> logic_indices;
  for ( uint64_t d = 0; d < D; ++ d ) {
    uint64_t i = logic_index % data_ -> logic_place_bases_ [ d ];
    logic_index /= data_ -> logic_place_bases_ [ d ];
    logic_indices . push_back ( i );
  }
  std::vector<uint64_t> order_indices;
  for ( uint64_t d = 0; d < D; ++ d ) {
    uint64_t i = order_index % data_ -> order_place_bases_ [ d ];
    order_index /= data_ -> order_place_bases_ [ d ];
    order_indices . push_back ( i );
  }

  std::vector<LogicParameter> logic;
  std::vector<OrderParameter> order;
  for ( uint64_t d = 0; d < D; ++ d ) {
    uint64_t n = data_ -> network_ . helper_network() . inputs ( d ) . size ();
    uint64_t m = data_ -> network_ . helper_network() . outputs ( d ) . size ();
    std::string hex_code = data_ -> factors_ [ d ] [ logic_indices[d] ];
    LogicParameter logic_param ( n, m, hex_code );
    OrderParameter order_param ( m, data_ -> order_index_to_helper_ [d] [ order_indices[d] ] );
    logic . push_back ( logic_param );
    order . push_back ( order_param );
  }
  Parameter result ( logic, order, data_ -> network_ . helper_network() );
  return result;
}

INLINE_IF_HEADER_ONLY uint64_t MultipleThresholdParameterGraph::
index ( Parameter const& p ) const {
  // Obtain logic and order information
  std::vector<LogicParameter> const& logic = p . logic ( );
  std::vector<OrderParameter> const& order = p . order ( );

  // Construct Logic indices
  std::vector<uint64_t> logic_indices;
  uint64_t D = data_ -> network_ . size ();
  for ( uint64_t d = 0; d < D; ++d ) {
    std::string hexcode = logic [ d ] . hex ( );
    auto it = data_ -> factors_inv_[d] . find ( hexcode );
    if ( it != data_ -> factors_inv_[d] . end ( )  ) {
      logic_indices . push_back ( it -> second );
    } else {
      return -1;
    }
  }

  // Construct Order indices
  std::vector<uint64_t> order_indices;
  for ( uint64_t d = 0; d < D; ++ d ) {
    if ( data_ -> helper_to_order_index_ [ d ].find(order[d].index()) == data_ -> helper_to_order_index_ [ d ].end() ) {
      return -1;
    } else {
      order_indices . push_back ( data_ -> helper_to_order_index_ [ d ][ order[d].index() ] );
    }
  }

  // Construct index
  uint64_t logic_index = 0;
  uint64_t order_index = 0;
  for ( uint64_t d = 0; d < D; ++ d ) {
    logic_index += data_ -> logic_place_values_[d] * logic_indices[d];
    order_index += data_ -> order_place_values_[d] * order_indices[d];
  }
  uint64_t index = order_index * data_ -> fixedordersize_ + logic_index;

  return (index < size()) ? index : -1;
}

INLINE_IF_HEADER_ONLY std::vector<uint64_t> MultipleThresholdParameterGraph::
adjacencies ( const uint64_t myindex, std::string const& type ) const {
  // The default value for type is "", which uses the default type "pre"
  std::string adj_type = type.empty() ? "pre" : type;
  if ( not ( adj_type == "pre" or adj_type == "fixedorder" or adj_type == "codim1" ) ) {
    throw std::runtime_error ( "Invalid adjacency type!" );
  }
  std::vector<uint64_t> output;
  Parameter p = parameter ( myindex );
  std::vector<LogicParameter> logics = p . logic ( );
  std::vector<OrderParameter> orders = p . order ( );

  uint64_t D = data_ -> network_ . size ( );

  std::vector<LogicParameter> logicsTmp = logics;
  std::vector<OrderParameter> ordersTmp = orders;

  // Check if order adjacency correspond to a co-dim 1 boundary
  auto codim1_adj_order = [&]( OrderParameter op_adj, uint64_t d ) {
    // Get permutations for this and adjacent order parameters
    std::vector<uint64_t> op_perm = orders [ d ] . permutation ( );
    std::vector<uint64_t> adj_perm = op_adj . permutation ( );
    // Get indices of permuted thresholds (should be 2)
    std::vector<uint64_t> perm_thres;
    for ( uint64_t i = 0; i < op_perm . size (); ++ i ) {
      if ( not ( op_perm [i] == adj_perm [i] ) ) {
        perm_thres . push_back (i);
      }
    }
    // Number of permuted thresholds should be 2
    if ( not ( perm_thres . size () == 2 ) ) {
      throw std::runtime_error ( "Invalid adjacent order!" );
    }
    // Now check if adjacent order if a co-dim 1 order
    // Indices of the swapped thresholds
    uint64_t j0 = perm_thres [0];
    uint64_t j1 = perm_thres [1];
    // Get input/output sizes information
    uint64_t n = data_ -> network_ . helper_network() . inputs ( d ) . size ();
    uint64_t m = data_ -> network_ . helper_network() . outputs ( d ) . size ();
    uint64_t N = ( 1LL << n );
    // The adjacent order is a co-dim 1 order if there is no
    // input combination (p_i) in between the two thresholds
    // that got swapped. This is true if both thresholds
    // produce the same signs for all input combinations.
    for ( uint64_t i = 0; i < N; ++ i ) {
      // Return false if signs differ
      if ( logics [d] ( i * m + j0 ) != logics [d] ( i * m + j1 ) ) {
        return false;
      }
    }
    return true;
  };

  // Compute adjacent order parameters if needed
  // For type fixedorder do not want adjacent orders
  if ( not ( type == "fixedorder" ) ) {
    for ( uint64_t d = 0; d < D; ++d ) {
      std::vector<OrderParameter> op_adjacencies = orders [ d ] . adjacencies ( );
      if ( op_adjacencies.size() > 0 ) {
        for ( auto op_adj : op_adjacencies ) {
          // Check if adj order is co-dim 1 for type codim1
          if ( ( type == "codim1" ) and ( not codim1_adj_order ( op_adj, d ) ) )
            continue;
          // Add adjacency order to list of adjacent parameters
          orders [ d ] = op_adj;
          Parameter adj_p ( logics, orders, data_ -> network_.helper_network() );
          uint64_t index_adj = MultipleThresholdParameterGraph::index ( adj_p );
          if ( index_adj != -1 ) { output . push_back ( index_adj ); }
          orders [ d ] = ordersTmp [ d ];
        }
      }
    }
  }
  // Compute adjacent logic parameters
  for ( uint64_t d = 0; d < D; ++d ) {
    std::vector<LogicParameter> lp_adjacencies = logics [ d ] . adjacencies ( );
    for ( auto lp_adj : lp_adjacencies ) {
      if ( data_ -> factors_inv_[d] . count ( lp_adj . hex ( ) ) == 0 ) { continue; }
      logics [ d ] = lp_adj;
      Parameter adj_p ( logics, orders, data_ -> network_.helper_network() );
      uint64_t index_adj = MultipleThresholdParameterGraph::index ( adj_p );
      if ( index_adj != -1 ) { output . push_back ( index_adj ); }
      logics [ d ] = logicsTmp [ d ];
    }
  }
  std::sort ( output . begin ( ), output . end ( ) );
  return output;
}

INLINE_IF_HEADER_ONLY MultipleThresholdNetwork const MultipleThresholdParameterGraph::
network ( void ) const {
  return data_ -> network_;
}

INLINE_IF_HEADER_ONLY std::ostream& operator << ( std::ostream& stream, MultipleThresholdParameterGraph const& pg ) {
  stream <<  "(MultipleThresholdParameterGraph: "<< pg.size() << " parameters, "
         << pg.network().size() << " nodes)";
  return stream;
}

INLINE_IF_HEADER_ONLY uint64_t MultipleThresholdParameterGraph::
fixedordersize ( void ) const {
  return data_ -> fixedordersize_;
}

INLINE_IF_HEADER_ONLY uint64_t MultipleThresholdParameterGraph::
reorderings ( void ) const {
  return data_ -> reorderings_;
}

INLINE_IF_HEADER_ONLY uint64_t MultipleThresholdParameterGraph::
_factorial ( uint64_t m ) const {
  static const std::vector<uint64_t> table =
    { 1, 1, 2, 6, 24, 120, 720, 5040, 40320, 362880};
  if ( m < 10 ) return table [ m ]; else return m * _factorial ( m - 1 );
}

INLINE_IF_HEADER_ONLY std::vector<uint64_t> MultipleThresholdParameterGraph::
_index_to_tail_rep ( uint64_t index ) {
  std::vector<uint64_t> tail_rep;
  uint64_t i = 1;
  while ( index > 0 ) {
    tail_rep . push_back ( (uint64_t) ( index % (uint64_t) i ) );
    index /= (uint64_t) i;
    ++ i;
  }
  return tail_rep;
}

INLINE_IF_HEADER_ONLY std::vector<uint64_t> MultipleThresholdParameterGraph::
_tail_rep_to_perm ( std::vector<uint64_t> const& tail_rep ) {
  // Note: This algorithm is suboptimal. It requires O(n^2) time
  //       but there is an O(n log n) algorithm. An optimal
  //       algorithm requires a counter tree (Red-Black tree which
  //       keeps counts of descendant elements and allows for rank
  //       based queries and insertions)
  std::vector<uint64_t> perm = tail_rep;
  uint64_t m = tail_rep . size ();
  std::reverse ( perm.begin(), perm.end() );
  for ( uint64_t i = 0; i < m; ++ i ) {
    for ( uint64_t j = 0; j < i; ++ j ) {
      if ( perm[m-j-1] >= tail_rep[i] ) ++ perm[m-j-1];
    }
  }
  return perm;
}