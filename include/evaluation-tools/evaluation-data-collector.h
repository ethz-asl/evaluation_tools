#ifndef EVALUATION_TOOLS_EVALUATION_DATA_COLLECTOR_H_
#define EVALUATION_TOOLS_EVALUATION_DATA_COLLECTOR_H_

#include <mutex>
#include <string>
#include <unordered_map>

#include <aslam/common/unique-id.h>
#include <Eigen/Core>

#include "evaluation-tools/internal/channel.h"

namespace evaluation {
namespace internal {
class EvaluationDataCollectorImpl;
class EvaluationDataCollectorDummy;
}

template<typename DataType> class Channel;

#define ENABLE_DATA_COLLECTOR 1

#ifdef ENABLE_DATA_COLLECTOR
  typedef internal::EvaluationDataCollectorImpl EvaluationDataCollector;
#else
  typedef internal::EvaluationDataCollectorDummy EvaluationDataCollector;
#endif

namespace internal {
/// \class VizDataCollector
/// \brief This class is implemented as a singleton to collect arbitrary visualization data that
///        can be associated with an aslam::NFrame id. A visualizer can be triggered to fetch
///        all data associated with a given NFrameId and render a view from it. The bound the
///        memory there is an upper limit on the number NFrameId slots the visualizer should
///        therefore free processed slots.
///        An e.g. storage layout could look like this:
///        VizDataCollector (global singleton) -->  NFrameId0 --> Channel ("nframe")
///                                                           --> Channel ("outlier_tracks")
///                                            -->  NFrameId1 --> Channel ("nframe")
///                                                           --> Channel ("awsome_coffee_mug")
///                                                           --> Channel ("outlier_tracks")
class EvaluationDataCollectorImpl {
 public:
  EIGEN_MAKE_ALIGNED_OPERATOR_NEW
  typedef internal::ChannelGroup ChannelGroup;
  typedef aslam::NFramesId SlotId;
  template<typename DataType> class PrintChannel;
  template<typename DataType> class PrintCommonChannel;
 private:
  // Singleton class.
  EvaluationDataCollectorImpl() = default;
  EvaluationDataCollectorImpl(const EvaluationDataCollectorImpl&) = delete;

 public:
  static EvaluationDataCollectorImpl& Instance() {
    static EvaluationDataCollectorImpl instance;
    return instance;
  }
  ~EvaluationDataCollectorImpl() = default;

  void reset() {
    std::lock_guard<std::mutex> lock(m_channel_groups_);
    channel_groups_.clear();
  }

  //////////////////////////////////////////////////////////////
  /// \name Channel level operations
  /// @{
 public:
  /// Methods to store and access data indexed by a SlotId.
  template<typename DataType>
  void pushData(const SlotId& slot_id, const std::string& channel_name, const DataType& data);
  template<typename DataType>
  bool getDataSafe(const SlotId& slot_id, const std::string& channel_name,
                   const DataType** data) const;
  bool hasChannel(const SlotId& slot_id, const std::string& channel_name) const;
  template<typename DataType>
  std::string printData(const SlotId& slot_id, const std::string& channel_name) const;

  /// Methods to access a common slot for store and access unindexed data.
  template<typename DataType>
  void pushCommonData(const std::string& channel_name, const DataType& data) {
    return pushData<DataType>(kCommonSlotId, channel_name, data);
  }
  template<typename DataType>
  bool getCommonDataSafe(const std::string& channel_name, const DataType** data) const {
    return getDataSafe<DataType>(kCommonSlotId, channel_name, data);
  }
  bool hasCommonChannel(const std::string& channel_name) const {
    return hasChannel(kCommonSlotId, channel_name);
  }
  template<typename DataType>
  std::string printCommonData(const std::string& channel_name) const {
    return printData<DataType>(kCommonSlotId, channel_name);
  }
  /// @}

  //////////////////////////////////////////////////////////////
  /// \name Slot level operations
  /// @{
 public:
  bool hasSlot(const SlotId& slot_id) const;
  void removeSlotIfAvailable(const SlotId& slot_id);

 private:
  ChannelGroup* getSlot(const SlotId& slot_id);
  const ChannelGroup* getSlot(const SlotId& slot_id) const;
  ChannelGroup* getSlotAndCreateIfNecessary(const SlotId& slot_id);
  /// @}

 protected:
  static const SlotId kCommonSlotId;

 private:
  typedef std::unordered_map<SlotId, ChannelGroup> SlotIdSlotMap;
  SlotIdSlotMap channel_groups_;
  mutable std::mutex m_channel_groups_;
};

/// \class DummyVizDataCollector
/// \brief A dummy class that has the visualization interface but does nothing.
class EvaluationDataCollectorDummy {
 public:
  template<typename DataType> class PrintChannel;
  typedef EvaluationDataCollectorImpl::SlotId SlotId;

 private:
  // Singleton class.
  EvaluationDataCollectorDummy() = default;
  EvaluationDataCollectorDummy(const EvaluationDataCollectorDummy&) = delete;

 public:
  static EvaluationDataCollectorDummy& Instance() {
    static EvaluationDataCollectorDummy instance;
    return instance;
  }
  ~EvaluationDataCollectorDummy() = default;
  void reset() {}

  //////////////////////////////////////////////////////////////
  /// \name Channel level operations
  /// @{
 public:
  /// Methods to store and access data indexed by a SlotId.
  template<typename DataType>
  void pushData(const SlotId& /*slot_id*/, const std::string& /*channel_name*/,
                const DataType& /*data*/) {}
  template<typename DataType>
  bool getDataSafe(const SlotId& /*slot_id*/, const std::string& /*channel_name*/,
                   const DataType** /*data*/) const {
    return false;
  }
  bool hasChannel(const SlotId& /*slot_id*/, const std::string& /*channel_name*/) const {
    return false;
  }
  template<typename DataType>
  std::string printData(const SlotId& /*slot_id*/, const std::string& /*channel_name*/) const {
    return std::string("");
  }

  /// Methods to access a common slot for store and access unindexed data.
  template<typename DataType>
  void pushCommonData(const std::string& /*channel_name*/, const DataType& /*data*/) {}
  template<typename DataType>
  bool getCommonDataSafe(const std::string& /*channel_name*/, const DataType** /*data*/) const {
    return false;
  }
  bool hasCommonChannel(const std::string& /*channel_name*/) const {
    return false;
  }
  template<typename DataType>
  std::string printCommonData(const std::string& /*channel_name*/) {
    return std::string("");
  }
  /// @}

  //////////////////////////////////////////////////////////////
  /// \name Slot level operations
  /// @{
 public:
  bool hasSlot(const SlotId& /*slot_id*/) const {
    return false;
  }
  void removeSlotIfAvailable(const SlotId& /*slot_id*/) {}
  /// @}
};

/// \class PrintChannel
/// \brief Helper to conveniently print channels that implement an operator<<
/// \code LOG(INFO) << VizCollector::PrintChannel<size_t>(slot_id, "channel_name");
template<typename DataType>
class EvaluationDataCollectorImpl::PrintChannel {
 public:
  friend EvaluationDataCollectorImpl;
  explicit PrintChannel(const EvaluationDataCollectorImpl::SlotId& slot_id,
                        const std::string& channel_name)
      : slot_id_(slot_id), channel_name_(channel_name) {}

  explicit PrintChannel(const std::string& channel_name)
      : slot_id_(EvaluationDataCollectorImpl::kCommonSlotId), channel_name_(channel_name) {}

  inline friend std::ostream& operator<<(std::ostream& out,
                                         const PrintChannel<DataType>& channel) {
    out << EvaluationDataCollectorImpl::Instance().printData<DataType>(channel.slot_id_,
                                                                channel.channel_name_);
    return out;
  }
 private:
  const EvaluationDataCollectorImpl::SlotId& slot_id_;
  const std::string& channel_name_;
};

template<typename DataType>
class EvaluationDataCollectorDummy::PrintChannel {
 public:
  friend EvaluationDataCollectorDummy;
  explicit PrintChannel(const EvaluationDataCollectorImpl::SlotId&, const std::string&) {}
  explicit PrintChannel(const std::string&) {}
  inline friend std::ostream& operator<<(std::ostream& out, const PrintChannel<DataType>&) {
    out << "NA";
    return out;
  }
};

}  // namespace internal
}  // namespace evaluation
#include "internal/evaluation-data-collector-inl.h"
#endif  // EVALUATION_TOOLS_EVALUATION_DATA_COLLECTOR_H_
