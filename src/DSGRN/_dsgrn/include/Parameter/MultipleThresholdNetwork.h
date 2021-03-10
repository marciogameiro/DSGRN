/// MultipleThresholdNetwork.h
/// Shaun Harker
/// 2015-05-22
///
/// Marcio Gameiro
/// 2021-01-02
///
/// Adam Zheleznyak
/// 2021-02-19

#pragma once

#include "common.h"

#include "Parameter/Network.h"

class MultipleThresholdNetwork_;

/// MultipleThresholdNetwork
///   This class holds network data.
///     * Loads specification files
///     * Outputs Graphviz visualizations
///     * Provides an interface to networks
class MultipleThresholdNetwork {
public:
  /// constructor
  MultipleThresholdNetwork ( void );

  /// MultipleThresholdNetwork
  ///   Construct network
  ///   If s contains a colon character (i.e. ':') it assumes s is a network specification.
  ///   Otherwise, it assumes s is a filename and attempts to load a network specification.
  MultipleThresholdNetwork ( std::string const& s );
  
  /// helper_network
  ///   Returns the regular network used to model the multiple threshold network
  Network const&
  helper_network ( void ) const;
  
  /// assign
  ///   Delayed construction of default constructed object
  void
  assign ( std::string const& s );
  
  /// load
  ///   load from network specification file
  void 
  load ( std::string const& filename );

  /// size
  ///   Return the number of nodes in the network
  uint64_t
  size ( void ) const;

  /// index
  ///   Return index of node given name string
  uint64_t 
  index ( std::string const& name ) const;

  /// name
  ///   Return name of node (given by index)
  std::string const&
  name ( uint64_t index ) const;

  /// inputs
  ///   Return a list of inputs to a node
  std::vector<uint64_t> const&
  inputs ( uint64_t index ) const;

  /// outputs
  ///   Return a list of outputs to a node
  std::vector<uint64_t> const&
  outputs ( uint64_t index ) const;

  /// logic
  ///   Return the logic of a node (given by index)
  std::vector<std::vector<uint64_t>> const&
  logic ( uint64_t index ) const;

  /// essential
  ///   Return whether or not to use only essential logic parameters
  bool
  essential ( uint64_t index ) const;

  /// interaction
  ///   Return the interaction type of an edge:
  ///   False for repression, true for activation
  std::vector<bool>
  interaction ( uint64_t source, uint64_t target ) const;

  /// order
  ///   Return the out-edge order number of an edge, i.e. so
  ///   outputs(source)[order(source,target,instance)] == target
//  uint64_t
//  order ( uint64_t source, uint64_t target, uint64_t instance ) const;
  uint64_t
  order ( uint64_t source, uint64_t target ) const;

  /// domains
  ///   Return a list consisting of the number of 
  ///   domains across (i.e. number of out-edges plus one)
  ///   for each dimension (i.e. network node)
  std::vector<uint64_t>
  domains ( void ) const;

  /// specification
  ///    Return the specification string (i.e. network spec file)
  std::string
  specification ( void ) const;

  /// graphviz
  ///   Return a graphviz string (dot language)
  std::string
  graphviz ( std::vector<std::string> const& theme = 
  { "aliceblue", // background color
    "beige",     // node color
    "black", "darkgoldenrod", "blue", "orange", "red", "yellow" // edge group colors
  } ) const;

  /// operator <<
//  friend std::ostream& operator << ( std::ostream& stream, MultipleThresholdNetwork const& network );

private:
  std::shared_ptr<MultipleThresholdNetwork_> data_;

  std::vector<std::string> _lines ( void );
  void _parse ( std::vector<std::string> const& lines );
};

struct MultipleThresholdNetwork_ {
  std::vector<std::vector<uint64_t>> inputs_;
  std::vector<std::vector<uint64_t>> outputs_;
  std::unordered_map<std::string, uint64_t> index_by_name_;
  std::vector<std::string> name_by_index_;
  std::unordered_map<std::pair<uint64_t,uint64_t>, std::vector<bool>, dsgrn::hash<std::pair<uint64_t,uint64_t>>> edge_type_;
  // Use (source, target, instance) to allow multiple edges
  // TODO: Use unordered_map to make it more efficient
  std::map<std::tuple<uint64_t,uint64_t>, uint64_t> order_;
//  std::map<std::tuple<uint64_t,uint64_t,uint64_t>, uint64_t> order_;
  // std::unordered_map<std::pair<uint64_t,uint64_t>, uint64_t, dsgrn::hash<std::pair<uint64_t,uint64_t>>> order_;
  std::vector<std::vector<std::vector<uint64_t>>> logic_by_index_;
  std::vector<bool> essential_;
  std::string specification_;
  Network helper_network_;
};

/// Python Bindings

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
namespace py = pybind11;

inline void
MultipleThresholdNetworkBinding (py::module &m) {
  py::class_<MultipleThresholdNetwork, std::shared_ptr<MultipleThresholdNetwork>>(m, "MultipleThresholdNetwork")
    .def(py::init<>())
    .def(py::init<std::string const&>())
    .def("load", &MultipleThresholdNetwork::load)
    .def("assign", &MultipleThresholdNetwork::assign)
    .def("size", &MultipleThresholdNetwork::size)
    .def("index", &MultipleThresholdNetwork::index)
    .def("name", &MultipleThresholdNetwork::name)
    .def("inputs", &MultipleThresholdNetwork::inputs)
    .def("outputs", &MultipleThresholdNetwork::outputs)
    .def("logic", &MultipleThresholdNetwork::logic)
    .def("essential", &MultipleThresholdNetwork::essential)
    .def("interaction", &MultipleThresholdNetwork::interaction)
    .def("order", &MultipleThresholdNetwork::order)
    .def("domains", &MultipleThresholdNetwork::domains)
    .def("specification", &MultipleThresholdNetwork::specification)
    .def("graphviz", [](MultipleThresholdNetwork const& network){ return network.graphviz();})
    .def("helper_network", &MultipleThresholdNetwork::helper_network)
    .def(py::pickle(
    [](MultipleThresholdNetwork const& p) { // __getstate__
        /* Return a tuple that fully encodes the state of the object */
        return py::make_tuple(p.specification());
    },
    [](py::tuple t) { // __setstate__
        if (t.size() != 1)
            throw std::runtime_error("Unpickling MultipleThresholdNetwork object: Invalid state!");
        /* Create a new C++ instance */
        return MultipleThresholdNetwork(t[0].cast<std::string>());
    }));
}
