#ifndef INTERNAL_EVALUATION_DATA_COLLECTOR_INL_H_
#define INTERNAL_EVALUATION_DATA_COLLECTOR_INL_H_

#include <mutex>
#include <string>
#include <unordered_map>

#include <aslam/common/time.h>
#include <aslam/common/unique-id.h>

namespace evaluation {
namespace internal {

template <class SlotIdType>
template<typename DataType>
void EvaluationDataCollectorImpl<SlotIdType>::pushData(
    const SlotId& slot_id, const std::string& channel_name, const DataType& data) {
  //LOG(INFO) << "Pushing data of slot id " << std::to_string(slot_id) << " to channel " << channel_name;
  ChannelGroup* slot = getSlotAndCreateIfNecessary(slot_id);
  CHECK_NOTNULL(slot);
  slot->setChannel(channel_name, data);
}

template <class SlotIdType>
template<typename DataType>
bool EvaluationDataCollectorImpl<SlotIdType>::getDataSafe(
    const SlotId& slot_id, const std::string& channel_name, const DataType** data) const {
  const ChannelGroup* slot;
  if ((slot = getSlot(slot_id)) == nullptr) {
    return false;
  }
  return slot->getChannelSafe(channel_name, data);
}

template <class SlotIdType>
template<typename DataType>
std::string EvaluationDataCollectorImpl<SlotIdType>::printData(
    const SlotId& slot_id, const std::string& channel_name) const {
  std::ostringstream out;
  const DataType* data;
  if (getDataSafe(slot_id, channel_name, &data)) {
    out << std::setprecision(5) << *CHECK_NOTNULL(data) << std::fixed;
  } else {
    out << "Channel not available.";
  }
  return out.str();
}

template <class SlotIdType>
typename EvaluationDataCollectorImpl<SlotIdType>::ChannelGroup* EvaluationDataCollectorImpl<SlotIdType>::getSlot(const SlotId& slot_id) {
  //CHECK(slot_id.isValid());
  std::lock_guard<std::mutex> lock(m_channel_groups_);

  typename SlotIdSlotMap::iterator it = channel_groups_.find(slot_id);
  if (it == channel_groups_.end()) {
    return nullptr;
  }
  return &it->second;
}

template <class SlotIdType>
const typename EvaluationDataCollectorImpl<SlotIdType>::ChannelGroup* EvaluationDataCollectorImpl<SlotIdType>::getSlot(
    const SlotId& slot_id) const {
  //CHECK(slot_id.isValid());
  std::lock_guard<std::mutex> lock(m_channel_groups_);
  typename SlotIdSlotMap::const_iterator it = channel_groups_.find(slot_id);
  if (it == channel_groups_.end()) {
    return nullptr;
  }
  return &it->second;
}

template <class SlotIdType>
typename EvaluationDataCollectorImpl<SlotIdType>::ChannelGroup* EvaluationDataCollectorImpl<SlotIdType>::getSlotAndCreateIfNecessary(
    const SlotId& slot_id) {
  //CHECK(slot_id.isValid());
  std::lock_guard<std::mutex> lock(m_channel_groups_);
  typename SlotIdSlotMap::iterator iterator;
  bool inserted = false;
  std::tie(iterator, inserted) = channel_groups_.emplace(std::piecewise_construct,
                                                         std::make_tuple(slot_id),
                                                         std::make_tuple());
  return &iterator->second;
}

template <class SlotIdType>
void EvaluationDataCollectorImpl<SlotIdType>::removeSlotIfAvailable(const SlotId& slot_id) {
  //CHECK(slot_id.isValid());
  std::lock_guard<std::mutex> lock(m_channel_groups_);
  channel_groups_.erase(slot_id);
}

template <class SlotIdType>
bool EvaluationDataCollectorImpl<SlotIdType>::hasSlot(const SlotId& slot_id) const {
  return (getSlot(slot_id) != nullptr);
}

template <class SlotIdType>
bool EvaluationDataCollectorImpl<SlotIdType>::hasChannel(const SlotId& slot_id,
                                      const std::string& channel_name) const {
  const ChannelGroup* slot;
  if ((slot = getSlot(slot_id)) == nullptr) {
    return false;
  }
  return slot->hasChannel(channel_name);
}

template <class SlotIdType>
void EvaluationDataCollectorImpl<SlotIdType>::getAllSlotIds(
    std::unordered_set<SlotId>* slot_ids) const {
  CHECK_NOTNULL(slot_ids)->clear();
  std::lock_guard<std::mutex> lock(m_channel_groups_);

  slot_ids->reserve(channel_groups_.size());
  for (const typename SlotIdSlotMap::value_type& slot_id_with_channel_group :
      channel_groups_) {
    if (slot_id_with_channel_group.first != kCommonSlotId) {
      slot_ids->emplace(slot_id_with_channel_group.first);
    }
  }
}
}  // namespace internal
}  // namespace evaluation
#endif  // INTERNAL_EVALUATION_DATA_COLLECTOR_INL_H_
