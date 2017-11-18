#ifndef EVALUATION_TOOLS_EVALUATION_DATA_COLLECTOR_H_
#define EVALUATION_TOOLS_EVALUATION_DATA_COLLECTOR_H_

#include <mutex>
#include <string>
#include <unordered_map>

#include <aslam/common/unique-id.h>
#include <diagnostic_updater/diagnostic_updater.h>
#include <Eigen/Core>
#include <ros/ros.h>

#include "evaluation-tools/internal/channel.h"

namespace evaluation {
namespace internal {
class EvaluationDataCollectorImpl;
class EvaluationDataCollectorDummy;
}

template<typename DataType> class Channel;

#define ENABLE_DATA_COLLECTOR

#ifdef ENABLE_DATA_COLLECTOR
  typedef internal::EvaluationDataCollectorImpl EvaluationDataCollector;
#else
  typedef internal::EvaluationDataCollectorDummy EvaluationDataCollector;
#endif

namespace internal {
/// \class EvaluationDataCollector
/// \brief This class is implemented as a singleton to collect arbitrary evaluation data that
///        can be associated with an aslam::NFrame id.
class EvaluationDataCollectorImpl {
 public:
  EIGEN_MAKE_ALIGNED_OPERATOR_NEW
  typedef internal::ChannelGroup ChannelGroup;
  typedef aslam::NFramesId SlotId;
  template<typename DataType> class PrintChannel;
  template<typename DataType> class PrintCommonChannel;
 private:
  // Singleton class.
  EvaluationDataCollectorImpl() {
    // Initialize ROS, if the host process doesn't initialize it itself.
    if (ros::isInitialized()) {
      VLOG(20) << "ROS is already initialized.";
    } else {
      int argv = 0;
      const std::string kNodeName = "evaluation_data_collector";
      ros::init(argv, nullptr, kNodeName);
    }

    node_handle_.reset(new ros::NodeHandle());
    const uint32_t kQueueSize = 1u;
    diagnostic_publisher_ =
        node_handle_->advertise<diagnostic_msgs::DiagnosticArray>(
            "/diagnostics", kQueueSize);

    //updater_.setHardwareID("evaluation_data_collector");
    //updater_.add(
    //    "test", this, &EvaluationDataCollectorImpl::produceDiagnostics);
  }
  EvaluationDataCollectorImpl(const EvaluationDataCollectorImpl&) = delete;
  virtual ~EvaluationDataCollectorImpl() = default;

  template<class DataType, bool>
  struct DiagnosticMessageWrapper final {
    EIGEN_MAKE_ALIGNED_OPERATOR_NEW
    DiagnosticMessageWrapper() = delete;
  };

  template<class DataType>
  struct DiagnosticMessageWrapper<DataType, true> {
    DiagnosticMessageWrapper(
        const SlotId& slot_id, const std::string& channel_name,
        const DataType& data_type, ros::Publisher* publisher) {
      CHECK_NOTNULL(publisher);

      diagnostic_msgs::DiagnosticStatus status;
      status.name = channel_name;
      status.hardware_id = "some_hardware_id";
      status.level = diagnostic_msgs::DiagnosticStatus::OK;
      status.message = std::to_string(data_type);
      diagnostic_msgs::DiagnosticArray msg;
      msg.status.emplace_back(status);
      msg.header.stamp = ros::Time::now(); // Add timestamp for ROS 0.10
      publisher->publish(msg);
    }
  };

  template<class DataType>
  struct DiagnosticMessageWrapper<DataType, false> {
    DiagnosticMessageWrapper(
        const SlotId& slot_id, const std::string& channel_name,
        const DataType& data_type, ros::Publisher* publisher) {}
  };

 public:
  static EvaluationDataCollectorImpl& Instance() {
    static EvaluationDataCollectorImpl instance;
    return instance;
  }

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
  template<bool B>
  void foo();
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
  void getAllSlotIds(std::unordered_set<SlotId>* slot_ids) const;

 private:
  ChannelGroup* getSlot(const SlotId& slot_id);
  const ChannelGroup* getSlot(const SlotId& slot_id) const;
  ChannelGroup* getSlotAndCreateIfNecessary(const SlotId& slot_id);

  void produceDiagnostics(diagnostic_updater::DiagnosticStatusWrapper& stat) {
    stat.name = "velodyne";
    stat.summary(diagnostic_msgs::DiagnosticStatus::WARN, "This is a silly updater.");
    stat.add("Stupidicity of this updater", 1000.);
  }
  /// @}

 protected:
  static const SlotId kCommonSlotId;

 private:
  typedef std::unordered_map<SlotId, ChannelGroup> SlotIdSlotMap;
  SlotIdSlotMap channel_groups_;
  mutable std::mutex m_channel_groups_;

  //diagnostic_updater::Updater updater_;

  std::unique_ptr<ros::NodeHandle> node_handle_;
  ros::Publisher diagnostic_publisher_;
};

/// \class DummyEvaluationDataCollector
/// \brief A dummy class that has the evaluation interface but does nothing.
class EvaluationDataCollectorDummy {
 public:
  template<typename DataType> class PrintChannel;
  typedef EvaluationDataCollectorImpl::SlotId SlotId;

 private:
  // Singleton class.
  EvaluationDataCollectorDummy() = default;
  EvaluationDataCollectorDummy(const EvaluationDataCollectorDummy&) = delete;
  virtual ~EvaluationDataCollectorDummy() = default;

 public:
  static EvaluationDataCollectorDummy& Instance() {
    static EvaluationDataCollectorDummy instance;
    return instance;
  }
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
  void getAllSlotIds(std::unordered_set<SlotId>* slot_ids) const {}
  /// @}
};

/// \class PrintChannel
/// \brief Helper to conveniently print channels that implement an operator<<
/// \code LOG(INFO) << EvaluationDataCollector::PrintChannel<size_t>(slot_id, "channel_name");
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
    out << EvaluationDataCollectorImpl::Instance().printData<DataType>(
        channel.slot_id_, channel.channel_name_);
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
  explicit PrintChannel(const EvaluationDataCollectorImpl::SlotId&, const std::string&) {};
  explicit PrintChannel(const std::string&) {};
  inline friend std::ostream& operator<<(std::ostream& out, const PrintChannel<DataType>&) {
    out << "NA";
    return out;
  }
};

}  // namespace internal
}  // namespace evaluation
#include "internal/evaluation-data-collector-inl.h"
#endif  // EVALUATION_TOOLS_EVALUATION_DATA_COLLECTOR_H_
