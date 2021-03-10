/// MultipleThresholdParameterGraph.h
/// Shaun Harker
/// 2015-05-24
/// Marcio Gameiro
/// 2020-10-06
/// Adam Zheleznyak
/// 2021-01-18


#pragma once 

#include "common.h"

#include "Parameter/Network.h"
#include "Parameter/MultipleThresholdNetwork.h"
#include "Parameter/Parameter.h" 
#include "Parameter/Configuration.h" 

struct MultipleThresholdParameterGraph_;

class MultipleThresholdParameterGraph {
public:
  /// constructor
  MultipleThresholdParameterGraph ( void );

  /// MultipleThresholdParameterGraph
  ///   Assign a network to the parameter graph
  ///   Search in path for logic .dat files
  MultipleThresholdParameterGraph ( MultipleThresholdNetwork const& network );

  /// assign
  ///   Assign a network to the parameter graph
  ///   Search in path for logic .dat files
  void
  assign ( MultipleThresholdNetwork const& network );

  /// size
  ///   Return the number of parameters
  uint64_t
  size ( void ) const;

  /// dimension
  ///   Return the number of nodes in the network
  ///   (i.e. the dimension of the phase space)
  uint64_t 
  dimension ( void ) const;

  /// logicsize
  ///   Given a network node 0 <= i < dimension(), 
  ///   Return the size of the factor graph associated
  ///   with network node i (for some fixed output edge ordering)
  uint64_t
  logicsize ( uint64_t i ) const;

  /// ordersize
  ///   Given a network node 0 <= i < dimension(), 
  ///   returns the number of output edge orderings
  ///   network().outputs().size() !
  uint64_t
  ordersize ( uint64_t i ) const;

  /// factorgraph
  ///   Return the list of hex-code strings
  ///   representing the logic parameters of the ith
  ///   ith factor graph
  std::vector<std::string> const& 
  factorgraph ( uint64_t i ) const;
  
  /// parameter
  ///   Return the parameter associated with an index
  Parameter
  parameter ( uint64_t index ) const;

  /// index
  ///   Return the index associated with a parameter
  ///   If the parameter presented is invalid, return -1
  uint64_t
  index ( Parameter const& p ) const;

  /// adjacencies
  ///   Return the adjacent parameter indices of the given type
  ///   to a given parameter index. The default type is used if
  ///   type is not specified.
  std::vector<uint64_t>
  adjacencies ( uint64_t const index, std::string const& type = "" ) const;

  /// network
  ///   Return network
  MultipleThresholdNetwork const
  network ( void ) const;

  /// fixedordersize
  ///   Return the number of parameters
  ///   for a fixed ordering
  uint64_t
  fixedordersize ( void ) const;

  /// reorderings
  ///   Return of reorderings
  ///   Note: size() = fixedordersize()*reorderings()
  uint64_t
  reorderings ( void ) const;

  /// operator <<
  ///   Stream out information about parameter graph.
  friend std::ostream& operator << ( std::ostream& stream, MultipleThresholdParameterGraph const& pg );

private:
  std::shared_ptr<MultipleThresholdParameterGraph_> data_;
  uint64_t _factorial ( uint64_t m ) const;
  std::vector<uint64_t> _powers_of_two ( uint64_t length ) const;
  static std::vector<uint64_t> _index_to_tail_rep ( uint64_t index );
  static std::vector<uint64_t> _tail_rep_to_perm ( std::vector<uint64_t> const& tail_rep );
};

struct MultipleThresholdParameterGraph_ {
  MultipleThresholdNetwork network_;
  uint64_t size_;
  uint64_t reorderings_;
  uint64_t fixedordersize_;
  std::vector<uint64_t> logic_place_values_;
  std::vector<uint64_t> order_place_values_;
  std::vector<std::vector<std::string>> factors_;
  std::vector<std::unordered_map<std::string,uint64_t>> factors_inv_;
  std::vector<uint64_t> logic_place_bases_;
  std::vector<uint64_t> order_place_bases_;
  std::vector<std::vector<uint64_t>> order_index_to_helper_;
  std::vector<std::unordered_map<std::uint64_t,uint64_t>> helper_to_order_index_;
};

/// Python Bindings

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
namespace py = pybind11;

inline void
MultipleThresholdParameterGraphBinding (py::module &m) {
  py::class_<MultipleThresholdParameterGraph, std::shared_ptr<MultipleThresholdParameterGraph>>(m, "MultipleThresholdParameterGraph")
    .def(py::init<>())
    .def(py::init<MultipleThresholdNetwork const&>())
    .def("size", &MultipleThresholdParameterGraph::size)
    .def("dimension", &MultipleThresholdParameterGraph::dimension)
    .def("logicsize", &MultipleThresholdParameterGraph::logicsize)
    .def("ordersize", &MultipleThresholdParameterGraph::ordersize)
    .def("factorgraph", &MultipleThresholdParameterGraph::factorgraph)
    .def("parameter", &MultipleThresholdParameterGraph::parameter)    
    .def("index", &MultipleThresholdParameterGraph::index)
    .def("adjacencies", &MultipleThresholdParameterGraph::adjacencies, py::arg("index"), py::arg("type") = "")
    .def("network", &MultipleThresholdParameterGraph::network)
    .def("fixedordersize", &MultipleThresholdParameterGraph::fixedordersize)
    .def("reorderings", &MultipleThresholdParameterGraph::reorderings)
    .def("__str__", [](MultipleThresholdParameterGraph * lp){ std::stringstream ss; ss << *lp; return ss.str(); })
    .def(py::pickle(
    [](MultipleThresholdParameterGraph const& p) { // __getstate__
        /* Return a tuple that fully encodes the state of the object */
        return py::make_tuple(p.network());
    },
    [](py::tuple t) { // __setstate__
        if (t.size() != 1)
            throw std::runtime_error("Unpickling MultipleThresholdParameterGraph object: Invalid state!");
        /* Create a new C++ instance */
        return MultipleThresholdParameterGraph(t[0].cast<MultipleThresholdNetwork>());
    }));
}
