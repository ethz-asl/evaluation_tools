#include "evaluation-tools/evaluation-data-collector.h"

namespace evaluation {
namespace internal {

template <>
const EvaluationDataCollectorImpl<int64_t>::SlotId EvaluationDataCollectorImpl<int64_t>::kCommonSlotId =
    aslam::time::getInvalidTime();

template <>
const EvaluationDataCollectorImpl<aslam::NFramesId>::SlotId EvaluationDataCollectorImpl<aslam::NFramesId>::kCommonSlotId =
    aslam::NFramesId::Random();

}  // namespace internal
}  // namespace evaluation

namespace std {
string to_string(const aslam::NFramesId& nframe_id) {
  return nframe_id.hexString();
}
}
