/// Parameter.hpp
/// Shaun Harker
/// 2015-05-24
///
/// Marcio Gameiro
/// 2023-09-30

#pragma once

#ifndef INLINE_IF_HEADER_ONLY
#define INLINE_IF_HEADER_ONLY
#endif

#include "Parameter.h"

INLINE_IF_HEADER_ONLY Parameter::
Parameter ( void ) {
  data_ . reset ( new Parameter_ );
}

INLINE_IF_HEADER_ONLY Parameter::
Parameter ( std::vector<LogicParameter> const& logic,
            std::vector<OrderParameter> const& order,
            Network const& network ) {
  assign ( logic, order, network );
}

INLINE_IF_HEADER_ONLY Parameter::
Parameter ( Network const& network ) {
  assign ( network );
}

INLINE_IF_HEADER_ONLY void Parameter::
assign ( std::vector<LogicParameter> const& logic,
         std::vector<OrderParameter> const& order,
         Network const& network ) {
  data_ . reset ( new Parameter_ );
  data_ -> logic_ = logic;
  data_ -> order_ = order;
  data_ -> network_ = network;
}

INLINE_IF_HEADER_ONLY void Parameter::
assign ( Network const& network ) {
  data_ . reset ( new Parameter_ );
  data_ -> network_ = network;
}

INLINE_IF_HEADER_ONLY bool Parameter::
attracting ( Domain const& dom ) const {
  int D = data_ -> network_ . size ();
  for ( int d = 0; d < D; ++ d ) {
    if ( not dom . isMin(d) && absorbing ( dom, d, -1 ) ) return false;
    if ( not dom . isMax(d) && absorbing ( dom, d, 1 ) ) return false;
  }
  return true;
}

INLINE_IF_HEADER_ONLY std::vector<bool> Parameter::
combination ( Domain const& dom, int variable ) const {
  std::vector<bool> input_combination;
  //std::cout << "  Forming input combination by analyzing inputs of node " << variable << ".\n";
  for ( int source : data_ -> network_ . inputs ( variable ) ) {
    //std::cout << "    Analyze source edge " << source << "\n";
    bool activating = data_ -> network_ . interaction ( source, variable );
    //std::cout << "      This edge is " << (activating ? "activating" : "repressing" ) << ".\n";
    int inedge = data_ -> network_ . order ( source, variable );
    //std::cout << "      This edge is the " << inedge << "th ordered outedge of " << source << ".\n";
    int thres = data_ -> order_ [ source ] . inverse ( inedge );
    //std::cout << "      The input combination digit depends on which side of threshold " << thres << " on dimension " << source << " we are at.\n";
    bool result = not ( dom [ source ] > thres ) ^ activating;
    //std::cout << "      The domain is on the " << ( ( dom [ source ] > thres ) ? "right" : "left" ) << " side of this threshold.\n";
    input_combination . push_back ( result );
    //std::cout << "      Hence, the input combination digit is " << (result ? "1" : "0") << "\n";
  } 
  //std::cout << "  Input combination formed. Big-endian representation = ";
  //for ( int i = input_combination . size () - 1; i >= 0; -- i ){
  // std::cout << (input_combination[i] ? "1" : "0");
  //}
  //std::cout << "\n";
  return input_combination;
}

INLINE_IF_HEADER_ONLY bool Parameter::
absorbing ( Domain const& dom, int collapse_dim, int direction ) const {
  //std::cout << "Absorbing (" << dom . index () << ", " << collapse_dim << ", " << direction << ")\n";
  int thres = dom [ collapse_dim ];
  if ( direction == -1 ) thres -= 1;
  if ( thres < 0 ) return false;
  if ( thres == data_ -> network_ . num_thresholds (collapse_dim) ) return false;
  // if ( thres == data_ -> network_ . outputs( collapse_dim).size() ) return false;
  //std::cout << "  Threshold # = " << thres << "\n";
  std::vector<bool> input_combination = combination(dom, collapse_dim);
  //std::cout << "  Consulting parameter " <<  data_ -> logic_ [ collapse_dim ] . stringify () << ".\n";
  bool flow_direction = data_ -> logic_ [ collapse_dim ] ( input_combination, thres );
  //std::cout << "  Flow direction is to the " << (flow_direction ? "right" : "left") << "\n";
  if ( direction == -1 ) {
    //std::cout << "  Hence the left wall is " << ((flow_direction)?"not ":"") << "absorbing.\n";
    return not flow_direction;
  } else {
    //std::cout << "  Hence the right wall is " << ((not flow_direction)?"not ":"") << "absorbing.\n";
    return flow_direction;
  }
}

INLINE_IF_HEADER_ONLY uint64_t Parameter::
regulator ( uint64_t variable, uint64_t threshold ) const {
  uint64_t num_outedges = network () . outputs ( variable ) . size ();
  // Return dimension if no out-edges
  if ( num_outedges == 0 ) {
    return network () . size ();
  }

  // If no extra thresholds (no self-edge threshold blowup)
  if ( network () . num_thresholds ( variable ) == num_outedges ) {
    uint64_t out_index = order () [ variable ] ( threshold );
    return network () . outputs ( variable ) [ out_index ];
  }

  // The variable "threshold" correspond to the domain threshold.
  // In case of self-edge threshold blowup this threshold may not
  // be one of the out-edge thresholds. So we find the corresponding
  // out-edge threshold and use it to get the target node.

  // Get self-edge threshold (return dimension if no self-edge)
  auto self_edge_threshold = [&]() {
    for ( uint64_t thresh = 0; thresh < num_outedges; ++ thresh ) {
      uint64_t out_index = order () [ variable ] ( thresh );
      uint64_t target = network () . outputs ( variable ) [ out_index ];
      if ( variable == target ) { // If self-edge
        return thresh; // Return thresh
      }
    }
    // No self-edge (return dimension)
    return network () . size ();
  };

  uint64_t out_edge_threshold = threshold;
  // If threshold is bigger than the self-edge threshold
  // we need to subtract the extra threshold from it
  if ( self_edge_threshold () < threshold ) {
    out_edge_threshold -= 1;
  }

  uint64_t out_index = order () [ variable ] ( out_edge_threshold );
  return network () . outputs ( variable ) [ out_index ];
}

INLINE_IF_HEADER_ONLY std::vector<uint64_t> Parameter::
labelling ( void ) const {
  std::vector<uint64_t> result;
  uint64_t D = network () . size ();

  // pre-allocated vectors (for efficiency)
  std::vector<uint64_t> lower_limits ( D );
  std::vector<uint64_t> upper_limits ( D );
  std::vector<uint64_t> dom ( D );
  std::vector<uint64_t> width ( D );

  std::vector<uint64_t> limits ( D );
  // std::vector<uint64_t> limits = network () . domains ();
  std::vector<uint64_t> jump ( D ); // index offset in each dim
  uint64_t N = 1;
  for ( uint64_t d = 0; d < D; ++ d ) {
    // Treat the no out edge case as one out edge
    uint64_t m = network() . outputs ( d ) . size ();
    limits [ d ] = (m ? m : 1) + 1;
    jump[d] =  N;
    N *= limits [ d ];
  }
  // N is now number of domains
  // Domains are implicitly indexed.
  // "jump" is an array telling us how much to change the index
  //   to move +1 in each dimension
  result . resize ( N, 0 );
  for ( int d = 0; d < D; ++ d ) {
    uint64_t n = network() . inputs ( d ) . size ();
    uint64_t numInComb = ( 1LL << n );
    //uint64_t num_debug_domains = 0;
    for ( uint64_t in = 0; in < numInComb; ++ in ) {
      /// What bin does the target point land in for dimension d?
      uint64_t bin = data_ -> logic_ [ d ] . bin ( in );
      /// Which domains have this input combination for dimension d?
      std::fill ( lower_limits.begin(), lower_limits.end(), 0 );
      upper_limits = limits;
      uint64_t sources = network () . inputs ( d ) . size ();
      for ( uint64_t inorder = 0; inorder < sources; ++ inorder ) {
        //std::cout << "Dim " << d << ", in = " << in << " inorder = " << inorder << "\n";
        uint64_t source = network () . inputs ( d ) [ inorder ];
        //std::cout << "source = " << source << "\n";
        bool activating = network () . interaction ( source, d );
        //std::cout << "high is activating? " << ( activating ? "yes" : "no" ) << "\n";
        int outorder = network () . order ( source, d );
        //std::cout << "outorder = " << outorder << "\n";
        bool side = in & ( 1LL << inorder );
        //std::cout << "on activating side? " << ( side ? "yes" : "no" ) << "\n";
        uint64_t thres = data_ -> order_ [ source ] . inverse ( outorder ) + 1;
        //std::cout << "critical bin = " << thres << "\n";
        if ( activating ^ side ) {
          //std::cout << "Case A.\n";
          lower_limits[source] = 0;
          upper_limits[source] = thres;
        } else {
          //std::cout << "Case B.\n";
          lower_limits[source] = thres;
          upper_limits[source] = limits [ source ];
        }
      }
      /// Iterate through two zones:
      ///   Zone 1. domain left of bin
      ///   Zone 2. domain right of bin
      ///   Note. domains matching bin do not
      ///         require anything to be done
      auto apply_mask = [&] ( uint64_t mask ) {
        // Iterate between lower and upper limits applying mask
        uint64_t dom_index = 0;
        dom = lower_limits;
        for ( uint64_t k = 0; k < D; ++ k ) {
          width[k] = upper_limits[k] - lower_limits[k];
          dom_index += jump[k] * lower_limits[k];
          if ( width[k] == 0 ) return;
        }
        while ( 1 ) {
          // apply mask
          result [ dom_index ] |= mask;
          // next domain
          for ( uint64_t k = 0; k < D; ++ k ) {
            ++ dom[k];
            dom_index += jump[k];
            if ( dom[k] < upper_limits[k] ) break;
            dom[k] = lower_limits[k];
            dom_index -= width[k] * jump[k];
          }
          // If we are back to start, return
          bool done = true;
          for ( uint64_t k = 0; k < D; ++ k ) {
            if ( dom[k] != lower_limits[k] ) done = false;
          }
          if ( done ) break;
        }
      };

      uint64_t left = lower_limits [ d ];
      uint64_t right = upper_limits [ d ];

      // Zone 1 (Flows to right)
      if ( bin > left ) {
        lower_limits [ d ] = left;
        // Bug fix for self repressor case
        upper_limits [ d ] = std::min ( right, bin );
        // upper_limits [ d ] = bin;
        apply_mask (1LL << (D+d));
      }
      // Zone 2 (Flows to left)
      if ( bin + 1 < right ) {
        // Bug fix for self repressor case
        lower_limits [ d ] = std::max ( left, bin + 1 );
        // lower_limits [ d ] = bin + 1;
        upper_limits [ d ] = right;
        apply_mask (1LL << d);
      }
    }
  }

  // Return result if not not doing any self-edge blowup
  if ( ( not network() . pos_edge_blowup () ) and ( not network() . neg_edge_blowup () ) ) {
    return result;
  }

  // Next we create an extended complex by blowing up the
  // co-dimension 1 faces defined by thresholds corresponding
  // to self (repressing) edges. We first blow up all the
  // co-dimension 1 faces, including the left most one in each
  // dimension (which is 0 and not defined by a thershold) but
  // not including the right most one (which is also not defined
  // by a thereshold), and assign the labellings to all the
  // domains from from the domains in the original (regular)
  // cell complex. We then discard the blowup domains not
  // corresponding to self (repressing) thresholds.
  //
  // Note: The labellings of the blowup domains which do not
  // correspond to self thresholds are not necessarily correct
  // as define below (but this is ok since these are the ones
  // to be discarded).

  // Create the data for the extended domain
  uint64_t N_ext = 1;
  for ( uint64_t d = 0; d < D; ++ d ) {
    N_ext *= 2 * limits [ d ];
  }

  // N_ext is now the number of extended domains
  std::vector<uint64_t> result_ext (N_ext, 0);
  // Flag domains to be removed at the end
  std::vector<bool> remove_domain (N_ext, false);
  for ( uint64_t dom_ext = 0; dom_ext < N_ext; ++ dom_ext ) {
    // Get regular domain index from extended domain index.
    // If extended domain is a regular domain get the index
    // of that regular domain. Otherwise get the index of the
    // next regular domain for each dimension in which the
    // extended domain does not coincide with a regular domain.
    uint64_t dom_reg = 0;
    uint64_t domain = dom_ext;
    bool keep_domain = true;
    std::vector<bool> regular_dom (D, true);
    std::vector<uint64_t> coords_ext (D);
    for ( uint64_t d = 0; d < D; ++ d ) {
      // Get coordinate of dom_ext in dimension d
      // Size of extended domain is 2 * limits
      coords_ext [d] = domain % (2 * limits [d]);
      domain /= (2 * limits [d]);
      if ( coords_ext [d] % 2 == 0 ) { // Not a regular domain
        regular_dom [d] = false;
        dom_reg += (coords_ext [d] / 2) * jump[d];
        if ( network() . outputs ( d ) .size () == 0 ) {
          // Not self threshold domain since no out edge
          keep_domain = false;
        } else if ( coords_ext [d] == 0 ) {
          // Remove left most domains
          keep_domain = false;
        } else { // coords_ext [d] > 0
          // Threshold that generate this domain
          uint64_t thres = coords_ext [d] / 2 - 1;
          // Original out edge order of threshold
          uint64_t j0 = data_ -> order_[d] (thres);
          // If target node for this out edge is not self
          if ( network() . outputs ( d ) [ j0 ] != d ) {
            keep_domain = false; // Not self threshold domain
          } // Do not blowup positive self edges if pos_edge_blowup is false
          else if ( ( not network() . pos_edge_blowup () ) and ( network() . interaction ( d, d ) ) ) {
            keep_domain = false; // Positive self edge blowup domain
          } // Do not blowup negative self edges if neg_edge_blowup is false
          else if ( ( not network() . neg_edge_blowup () ) and ( not network() . interaction ( d, d ) ) ) {
            keep_domain = false; // Negative self edge blowup domain
          }
        }
      } else { // Regular domain
        dom_reg += ((coords_ext [d] - 1) / 2) * jump[d];
      }
    }
    // Do not set labels if not regular or self threshold domain
    if ( not keep_domain ) {
      // Remove this domain at the end
      remove_domain [ dom_ext ] = true;
      continue;
    }
    // Use dom_reg to set label for dom_ext
    for ( uint64_t d = 0; d < D; ++ d ) {
      // Regular domains to be used to
      // set the left and right walls
      uint64_t dom_reg_left = dom_reg;
      uint64_t dom_reg_right = dom_reg;
      uint64_t mask_left = 1LL << d;
      uint64_t mask_right = 1LL << (D+d);
      if ( regular_dom [d] ) { // For regular domain just copy labels
        // Assuming that the n-th bit of x is 0, x |= y & (1LL << n)
        // sets the n-th bit of x to be the n-th bit of y, that is,
        // if the n-th bit of y is 0 then the n-th bit of x remains
        // 0, otherwise it is set to 1.
        result_ext [ dom_ext ] |= result [ dom_reg_left ] & mask_left;
        result_ext [ dom_ext ] |= result [ dom_reg_right ] & mask_right;
      } else { // Non-regular domain
        if ( coords_ext [d] == 0 ) {
          // Make it flow to the right, that is, leave
          // left label as 0 and set right label to 1
          result_ext [ dom_ext ] |= mask_right;
        } else {
          // Use previous domain in dim d for left wall
          dom_reg_left -= jump[d];
          // This is a non-regular domain in dimension d.
          // So we use the negation of the right wall label of
          // the left domain to set the left wall label of this
          // domain, and we use the negation of the left wall
          // label of the right domain to set the right wall
          // of this domain.
          if ( not (result [ dom_reg_left ] & mask_right) ) {
            result_ext [ dom_ext ] |= mask_left;
          }
          if ( not (result [ dom_reg_right ] & mask_left) ) {
            result_ext [ dom_ext ] |= mask_right;
          }
        }
      }
    }
  }

  result . clear ();

  // Remove blowup domains not corresponding to self-edges
  for ( uint64_t dom_ext = 0; dom_ext < N_ext; ++ dom_ext ) {
    if ( not remove_domain [ dom_ext ] ) {
      result . push_back (result_ext [ dom_ext ]);
    }
  }

  return result;
}

INLINE_IF_HEADER_ONLY Network const Parameter::
network ( void ) const {
  return data_ -> network_;
}

INLINE_IF_HEADER_ONLY std::string Parameter::
stringify ( void ) const {
  std::stringstream ss;
  uint64_t D = data_ -> network_ . size ();
  ss << "[";
  for ( uint64_t d = 0; d < D; ++ d ) {
    if ( d > 0 ) ss << ",";
    ss << "[\"" << network() . name ( d ) << "\","
       << data_ -> logic_[d] << "," << data_ -> order_[d] << "]";
  }
  ss << "]";
  return ss . str ();
}

INLINE_IF_HEADER_ONLY void Parameter::
parse ( std::string const& str ) {
  json p = json::parse(str);
  data_ -> logic_ . clear ();
  data_ -> order_ . clear ();
  for ( auto network_node : p ) {
    data_ -> logic_ . push_back ( LogicParameter () );
    data_ -> order_ . push_back ( OrderParameter () );
    // (*node)[0] has node name, which we ignore.
    data_ -> logic_ . back() . parse ( json::stringify ( network_node[1] )); //TODO inefficient
    data_ -> order_ . back() . parse ( json::stringify ( network_node[2] )); //TODO inefficient
  }
}

INLINE_IF_HEADER_ONLY std::string Parameter::
input_polynomial ( uint64_t in, uint64_t d ) const {
  std::stringstream input_ss;
  std::vector<std::vector<uint64_t>> logic = network () . logic ( d );
  std::string const& node_name = network() . name ( d );
  uint64_t n = network() . inputs ( d ) . size ();
  input_ss << "p" << in << " = ";
  // Corner case: n == 0 (no inputs)
  if ( n == 0 ) {
    input_ss << "B[" << node_name << "]";
    return input_ss . str ();
  }
  uint64_t bit = 1;
  uint64_t k = 0;
  for ( auto const& factor : logic ) {
    if ( factor . size () > 1 ) input_ss << "(";
    bool inner_first = true;
    for ( uint64_t source : factor ) {
      if ( inner_first ) inner_first = false; else input_ss << " + ";
      std::string source_name = network() . name( source );
      if ( in & bit ) {
        input_ss << "U[" << source_name << "->" << node_name << "]";
      } else {
        input_ss << "L[" << source_name << "->" << node_name << "]";
      }
      bit <<= 1;
      ++ k;
    }
    if ( factor . size () > 1 ) input_ss << ")"; 
    else if ( k < n ) input_ss << " ";
  }
  return input_ss . str ();
}

INLINE_IF_HEADER_ONLY std::string Parameter::
output_threshold ( uint64_t j, uint64_t d ) const {
  uint64_t target = network() . outputs ( d ) [ j ];
  std::string node_name = network() . name ( d );
  std::string target_name = network() . name(target);
  std::stringstream output_ss;
  output_ss << "t" << j << " = T[" << node_name << "->" << target_name << "]";
  return output_ss . str ();
}

INLINE_IF_HEADER_ONLY std::string Parameter::
partialorders ( std::string const& type ) const {
  // The default value for type is "", which uses the default type "t"
  std::string thres_type = type.empty() ? "t" : type;
  if ( not ( thres_type == "t" or thres_type == "T" ) ) {
    throw std::runtime_error ( "Invalid threshold type!" );
  }
  // Print parameter partial order
  uint64_t D = data_ -> network_ . size ();
  std::stringstream result_ss;
  for ( uint64_t d = 0; d < D; ++ d ) {
    uint64_t n = network() . inputs ( d ) . size ();
    uint64_t m = network() . outputs ( d ) . size ();
    uint64_t N = ( 1LL << n );
    // Upper bound threshold for p_i
    std::vector<uint64_t> upper_thres (N);
    // Get order of input combinations and thresholds
    for ( uint64_t i = 0; i < N; ++ i ) {
      uint64_t j = 0;
      while ( j < m && data_ -> logic_[d] ( i * m + j ) ) ++ j;
      upper_thres [i] = j; // Threshold such that p_i < T_j
    }
    // Get partial order as a vector of string
    std::vector<std::string> partial_order;
    for ( uint64_t j = 0; j <= m; ++ j ) {
      for ( uint64_t i = 0; i < N; ++ i ) {
        if ( upper_thres [i] == j ) { // If p_i < T_j
          std::stringstream p_ss;
          p_ss << "p" << i;
          partial_order . push_back ( p_ss . str () );
        }
      }
      if ( j < m ) { // If j == m then p_i > all thresholds
        // Get original out edge order
        uint64_t j0 = data_ -> order_[d](j);
        // Get output threshold in the format "tj = T[x->y]""
        std::string out_thres = output_threshold ( j0, d );
        // Split string at char '=' to get tj and T[x->y]
        std::stringstream thres_ss (out_thres);
        std::string thres_t_str; // Get tj
        std::getline (thres_ss, thres_t_str, '=');
        std::string thres_T_str; // Get T[x->y]
        std::getline (thres_ss, thres_T_str, '=');
        if ( thres_type == "t" ) {
          // Remove trailing whitespaces
          thres_t_str = std::regex_replace(thres_t_str, std::regex(" +$"), "");
          partial_order . push_back ( thres_t_str ); // Use tj
        } else { // thres_type == "T"
          // Remove leading whitespaces
          thres_T_str = std::regex_replace(thres_T_str, std::regex("^ +"), "");
          partial_order . push_back ( thres_T_str ); // Use T[x->y]
        }
      }
    }
    // Form output string
    std::string node_name = network() . name ( d );
    result_ss << node_name << " : (";
    bool first = true;
    for ( auto item_str : partial_order ) {
      if ( first ) {
        result_ss << item_str;
        first = false;
      } else {
        result_ss << ", " << item_str;
      }
    }
    if ( d < D - 1 ) {
      result_ss << ")\n";  
    } else {
      result_ss << ")";
    }
  }
  return result_ss . str ();
}

INLINE_IF_HEADER_ONLY std::string Parameter::
inequalities ( void ) const {
  // input_string
  //   Given an input edge i of a node d output the L/U indexing associated
  auto input_string = [&]( uint64_t i, uint64_t d ) {
    uint64_t source = network() . inputs ( d ) [ i ];
    std::string const& node_name = network() . name ( d );
    std::string source_name = network() . name(source);
    std::stringstream input_ss;
    // Modify indexing output format
    input_ss << "[" << source_name << "->" << node_name << "]";
    // input_ss << "[" << source_name << "," << node_name << "]";
    return input_ss . str ();
  };
  // output_string
  //   Given an output edge j, output the THETA variable associated with it
  auto output_string = [&]( uint64_t j, uint64_t d ) {
    std::string const& node_name = network() . name ( d );
    // For no out edge case
    std::string target_name = "";
    if ( network() . outputs ( d ) . size () ) {
      uint64_t target = network() . outputs ( d ) [ data_ -> order_[d](j) ];
      target_name = network() . name(target);
    }
    std::stringstream output_ss;
    // Modify indexing output format
    output_ss << "T[" << node_name << "->" << target_name << "]";
    // output_ss << "T[" << node_name << "," << target_name << "]";
    return output_ss . str ();
  };
  // input_combo_string
  //   Given an input combination i, return the algebraic formula
  //   of U's and L's associated with that input combination.
  auto input_combo_string = [&]( uint64_t i, uint64_t d ) {
    std::stringstream input_ss;
    std::vector<std::vector<uint64_t>> logic = 
      network () . logic ( d );
    std::string const& node_name = network() . name ( d );
    uint64_t n = network() . inputs ( d ) . size ();
    // Corner case: n == 0 (no inputs)
    if ( n == 0 ) {
      input_ss << "B[" << node_name << "]";
      return input_ss . str ();
    }
    uint64_t bit = 1;
    uint64_t k = 0;
    for ( auto const& factor : logic ) {
      if ( factor . size () > 1 ) input_ss << "(";
      bool inner_first = true;
      for ( uint64_t source : factor ) {
        if ( inner_first ) inner_first = false; else input_ss << " + ";
        std::string source_name = network() . name(source);
        if ( i & bit ) {
          // Modify indexing output format
          input_ss << "U[" << source_name << "->" << node_name << "]";
          // input_ss << "U[" << source_name << "," << node_name << "]";
        } else {
          // Modify indexing output format
          input_ss << "L[" << source_name << "->" << node_name << "]";
          // input_ss << "L[" << source_name << "," << node_name << "]";
        }
        bit <<= 1;
        ++ k;
      }
      if ( factor . size () > 1 ) input_ss << ")"; 
      else if ( k < n ) input_ss << " ";
    }
    return input_ss . str ();
  };

  std::stringstream ss;
  uint64_t D = data_ -> network_ . size ();
  ss << "{ \"inequalities\" : \"";

  bool outerfirst = true;
  for ( uint64_t d = 0; d < D; ++ d ) {
    if ( outerfirst ) outerfirst = false; else ss << " && ";
    uint64_t n = network() . inputs ( d ) . size ();
    // Treat the no out edge case as one out edge
    uint64_t m = network() . outputs ( d ) . size () ? network() . outputs ( d ) . size () : 1;
    uint64_t N = ( 1LL << n );
    // Output all inequalities comparing input formulas to thresholds
    bool first = true;
    for ( uint64_t i = 0; i < N; ++ i ) {
      if ( first ) first = false; else ss << " && ";
      uint64_t j = 0;
      while ( j < m && data_ -> logic_[d] ( m*i + j ) ) ++ j;
      if ( j == 0 ) {
        ss << input_combo_string ( i, d ) << " < " << output_string ( 0, d );
      } else if ( j == m ) {
        ss << output_string ( m-1, d ) << " < " << input_combo_string ( i, d );
      } else {
        ss << output_string ( j-1, d ) << " < " 
           << input_combo_string ( i, d ) << " < " 
           << output_string ( j, d );
      }
    }
    ss << " && ";
    // Output all inequalities comparing thresholds
    first = true;
    for ( uint64_t j = 0; j < m; ++ j ) {
      if ( first ) { 
        first = false;
        ss << "0 < ";
      } else { 
        ss << " < ";
      }
      ss << output_string ( j, d );
    }

    ss << " && ";
    if ( n == 0 ) {
      // Output 0 < B constraint (here, B is basal rate for zero-input node)
      ss << "0 < " << input_combo_string ( 0, d );
    } else {
      // Output 0 < L < U  constraints
      first = true;
      for ( uint64_t i = 0; i < n; ++ i ) {
        if ( first ) first = false; else ss << " && ";
        ss << "0 < L" << input_string ( i, d ) << " < U" << input_string ( i, d );
      }
    }

  }
  ss << "\", \"variables\" : \"{";
  // Output variable list
  outerfirst = true;
  for ( uint64_t d = 0; d < D; ++ d ) {
    uint64_t n = network() . inputs ( d ) . size ();
    // Treat the no out edge case as one out edge
    uint64_t m = network() . outputs ( d ) . size () ? network() . outputs ( d ) . size () : 1;
    if ( outerfirst ) outerfirst = false; else ss << ", ";
    for ( uint64_t i = 0; i < n; ++ i ) {
      ss << "L" << input_string ( i, d ) << ", ";
    }
    for ( uint64_t i = 0; i < n; ++ i ) {
      ss << "U" << input_string ( i, d ) << ", ";
    }
    bool first = true;
    for ( uint64_t j = 0; j < m; ++ j ) {
      if ( first ) first = false; else ss << ", ";
      ss << output_string ( j, d );
    }
  }
  ss << "}\"}";
  return ss . str ();
}

INLINE_IF_HEADER_ONLY std::vector<LogicParameter> const & Parameter::
logic ( void ) const {
    return data_ -> logic_;
}

INLINE_IF_HEADER_ONLY std::vector<OrderParameter> const & Parameter::
order ( void ) const {
    return data_ -> order_;
}

INLINE_IF_HEADER_ONLY std::ostream& operator << ( std::ostream& stream, Parameter const& p ) {
  stream << p.stringify();
  return stream;
}
