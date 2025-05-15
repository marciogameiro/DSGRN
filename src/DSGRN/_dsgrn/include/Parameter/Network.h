/// Network.h
/// Shaun Harker
/// 2015-05-22
///
/// Marcio Gameiro
/// 2024-12-01

#pragma once

#include "common.h"

class Network_;

/// Network
///   This class holds network data.
///     * Loads specification files
///     * Outputs Graphviz visualizations
///     * Provides an interface to networks
class Network {
public:
  /// constructor
  Network ( void );

  /// Network
  ///   Construct network
  ///   If s contains a colon character (i.e. ':') it assumes s is a network specification.
  ///   Otherwise, it assumes s is a filename and attempts to load a network specification.
  ///   Do a blowup of negative self-edges, positive self-edges, both, or none, if
  ///   edge_blowup == "neg", "pos", "all", or "none", respectively. The default is to do a
  ///   blowup of negative self-edges only.
  Network ( std::string const& s, std::string const& edge_blowup = "" );

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

  /// parameter_type
  ///   Return parameter type: DSGRN (D), Boolean (B), Multi-Boolean (M)
  char
  parameter_type ( uint64_t index ) const;

  /// interaction
  ///   Return the interaction type of an edge:
  ///   False for repression, true for activation
  bool
  interaction ( uint64_t source, uint64_t target ) const;

  /// pos_edge_blowup
  ///   Return whether or not to blowup positive self-edges
  bool
  pos_edge_blowup ( void ) const;

  /// neg_edge_blowup
  ///   Return whether or not to blowup negative self-edges
  bool
  neg_edge_blowup ( void ) const;

  /// num_thresholds
  ///   Return the number of thresholds
  uint64_t
  num_thresholds ( uint64_t index ) const;

  /// order
  ///   Return the out-edge order number of an edge, i.e. so
  ///   outputs(source)[order(source,target)] == target
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
  friend std::ostream& operator << ( std::ostream& stream, Network const& network );

private:
  std::shared_ptr<Network_> data_;

  std::vector<std::string> _lines ( void );
  void _parse ( std::vector<std::string> const& lines );
};

struct Network_ {
  std::vector<std::vector<uint64_t>> inputs_;
  std::vector<std::vector<uint64_t>> outputs_;
  std::unordered_map<std::string, uint64_t> index_by_name_;
  std::vector<std::string> name_by_index_;
  std::unordered_map<std::pair<uint64_t,uint64_t>, bool, dsgrn::hash<std::pair<uint64_t,uint64_t>>> edge_type_;
  std::unordered_map<std::pair<uint64_t,uint64_t>, uint64_t, dsgrn::hash<std::pair<uint64_t,uint64_t>>> order_;
  std::vector<std::vector<std::vector<uint64_t>>> logic_by_index_;
  std::vector<uint64_t> num_thresholds_; // Number of thresholds
  std::vector<char> parameter_type_; // DSGRN (D), Boolean (B), Multi-Boolean (M)
  std::vector<bool> essential_;
  std::string specification_;
  bool pos_edge_blowup_ = false; // Blowup positive self-edges if true
  bool neg_edge_blowup_ = true;  // Blowup negative self-edges if true
};

/// Python Bindings

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
namespace py = pybind11;

inline void
NetworkBinding (py::module &m) {
  py::class_<Network, std::shared_ptr<Network>>(m, "Network")
    .def(py::init<>())
    .def(py::init<std::string const&, std::string const&>(), py::arg("s"), py::arg("edge_blowup") = "")
    .def("load", &Network::load)
    .def("assign", &Network::assign)
    .def("size", &Network::size)
    .def("index", &Network::index)
    .def("name", &Network::name)
    .def("inputs", &Network::inputs)
    .def("outputs", &Network::outputs)
    .def("logic", &Network::logic)
    .def("essential", &Network::essential)
    .def("parameter_type", &Network::parameter_type)
    .def("interaction", &Network::interaction)
    .def("pos_edge_blowup", &Network::pos_edge_blowup)
    .def("neg_edge_blowup", &Network::neg_edge_blowup)
    .def("num_thresholds", &Network::num_thresholds)
    .def("order", &Network::order)
    .def("domains", &Network::domains)
    .def("specification", &Network::specification)
    .def("graphviz", [](Network const& network){ return network.graphviz();})
    .def(py::pickle(
    [](Network const& p) { // __getstate__
        /* Return a tuple that fully encodes the state of the object */
        return py::make_tuple(p.specification());
    },
    [](py::tuple t) { // __setstate__
        if (t.size() != 1)
            throw std::runtime_error("Unpickling Network object: Invalid state!");
        /* Create a new C++ instance */
        return Network(t[0].cast<std::string>());
    }));
}
